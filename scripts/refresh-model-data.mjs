#!/usr/bin/env node
/**
 * Refresh AI Match's benchmark data from the Artificial Analysis Data API.
 *
 *   node scripts/refresh-model-data.mjs            # write changes
 *   node scripts/refresh-model-data.mjs --dry-run  # report only, touch nothing
 *
 * Requires AA_API_KEY (free tier is enough). See docs/DATA_REFRESH.md.
 *
 * Design rule, non-negotiable: this script never invents a number. Every value it
 * writes was either returned by the API or derived by a formula checked against
 * published values. Anything it cannot source keeps its previous value and is
 * reported as stale — because a wrong benchmark number does not throw, it just
 * silently produces a confident, wrong ranking.
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const CONFIG_PATH = join(ROOT, 'scripts/models.config.json');
const DATA_PATH = join(ROOT, 'src/lib/model-data.json');
const API_BASE = 'https://artificialanalysis.ai/api/v2';

const DRY_RUN = process.argv.includes('--dry-run');
const API_KEY = process.env.AA_API_KEY;

const log = (...a) => console.log(...a);
const warn = (...a) => console.warn('  ! ', ...a);

/** Read a dotted path out of a nested object; undefined if any hop is missing. */
function dig(obj, path) {
  return path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
}

/**
 * First candidate path that yields a real number.
 * AA documents null as "not measured" — never coerce it to 0, which would look
 * like a legitimately terrible score and silently skew the entropy weights.
 */
function pick(obj, candidates) {
  for (const path of candidates) {
    const v = dig(obj, path);
    if (typeof v === 'number' && Number.isFinite(v)) return { value: v, path };
  }
  return null;
}

/** AA reports several evals as percentages; the site stores 0-1. */
function toUnitScale(key, v) {
  if (['inputPrice', 'outputPrice', 'costPerTask', 'tokenForIndex', 'apiSpeed'].includes(key)) return v;
  if (key === 'gdpvalAA') return v > 100 ? (v - 500) / 2000 : v; // Elo -> (Elo-500)/2000
  return v > 1 ? v / 100 : v;
}

async function apiGet(path) {
  const res = await fetch(API_BASE + path, {
    headers: { 'x-api-key': API_KEY, accept: 'application/json' },
  });
  const tier = res.headers.get('x-aa-tier');
  const remaining = res.headers.get('x-ratelimit-remaining');
  if (res.status === 401) throw new Error('AA_API_KEY rejected (401). Check the key is current.');
  if (res.status === 403) throw new Error(`Endpoint ${path} needs a higher tier than "${tier}".`);
  if (res.status === 429) {
    throw new Error(`Rate limit exhausted. Resets at ${res.headers.get('x-ratelimit-reset')}.`);
  }
  if (!res.ok) throw new Error(`${path} -> HTTP ${res.status}`);
  const body = await res.json();
  log(`  fetched ${path}  (tier=${tier}, ${remaining} requests left today)`);
  return body;
}

/**
 * AA publishes Omniscience accuracy and index for every model, but the
 * hallucination rate for only a subset. Derive it:
 *     hallucination = (accuracy - index/100) / (1 - accuracy)
 * Verified exact (~1e-16) against every model AA does publish.
 */
function deriveNonHallucination(model, cfg) {
  const acc = pick(model, cfg.derived.omniNonHall.inputs.accuracy);
  const idx = pick(model, cfg.derived.omniNonHall.inputs.omniscienceIndex);
  if (!acc || !idx) return null;
  const a = acc.value > 1 ? acc.value / 100 : acc.value;
  if (a >= 1) return null;
  const hallucination = (a - idx.value / 100) / (1 - a);
  const nonHall = 1 - hallucination;
  if (!Number.isFinite(nonHall) || nonHall < 0 || nonHall > 1) return null;
  return Number(nonHall.toFixed(3));
}

/** Flag any model that outranks a tracked slot, without changing anything. */
function findNewer(allModels, slot, current) {
  const currentScore = current?.artificial_analysis_intelligence_index ?? -Infinity;
  return allModels
    .filter((m) => {
      const creator = (m.model_creator?.slug ?? m.model_creator?.name ?? '').toLowerCase();
      return slot.creatorMatch.some((c) => creator.includes(c));
    })
    .filter((m) => (m.artificial_analysis_intelligence_index ?? -Infinity) > currentScore)
    .filter((m) => m.slug !== slot.aaSlug)
    .sort(
      (a, b) =>
        (b.artificial_analysis_intelligence_index ?? 0) -
        (a.artificial_analysis_intelligence_index ?? 0),
    );
}

async function main() {
  if (!API_KEY) {
    console.error(
      '\nAA_API_KEY is not set.\n\n' +
        'Get a free key at https://artificialanalysis.ai/data-api, then:\n' +
        '  export AA_API_KEY=your_key_here\n\n' +
        'See docs/DATA_REFRESH.md for the full setup.\n',
    );
    process.exit(1);
  }

  const cfg = JSON.parse(readFileSync(CONFIG_PATH, 'utf8'));
  const data = JSON.parse(readFileSync(DATA_PATH, 'utf8'));

  log('\nFetching Artificial Analysis language models...');
  const payload = await apiGet('/language/models/free');
  const all = payload.data ?? [];
  log(`  ${all.length} models returned, intelligence_index_version=${payload.intelligence_index_version}`);

  if (String(payload.intelligence_index_version) !== String(cfg.intelligenceIndexVersion)) {
    warn(
      `Intelligence Index version changed: ${cfg.intelligenceIndexVersion} -> ` +
        `${payload.intelligence_index_version}. Scores may not be comparable to the ` +
        `paper's tables. Review before merging.`,
    );
  }

  const bySlug = new Map(all.map((m) => [m.slug, m]));
  const changes = [];
  const staleReport = [];
  const newerReport = [];

  for (const slot of cfg.slots) {
    const model = data.models.find((m) => m.id === slot.id);
    if (!model) {
      warn(`slot "${slot.slot}": ${slot.id} missing from model-data.json, skipping`);
      continue;
    }
    log(`\n${model.name}`);

    const api = bySlug.get(slot.aaSlug);
    if (!api) {
      warn(`not found in API under slug "${slot.aaSlug}" — all indicators kept, marked stale`);
      staleReport.push({ model: model.name, fields: ['(entire model)'] });
      model.provenance.stale = Object.keys(model.indicators);
      continue;
    }

    const stale = [];
    for (const [key, candidates] of Object.entries(cfg.indicatorMap)) {
      if (key.startsWith('$')) continue;
      const hit = pick(api, candidates);
      if (!hit) {
        stale.push(key);
        warn(`${key}: not in API response — keeping ${model.indicators[key]}`);
        continue;
      }
      const next = Number(toUnitScale(key, hit.value).toFixed(3));
      const prev = model.indicators[key];
      if (next !== prev) {
        changes.push({ model: model.name, key, prev, next });
        log(`    ${key}: ${prev} -> ${next}`);
      }
      model.indicators[key] = next;
    }

    const nonHall = deriveNonHallucination(api, cfg);
    if (nonHall == null) {
      stale.push('omniNonHall');
      warn(`omniNonHall: inputs unavailable — keeping ${model.indicators.omniNonHall}`);
    } else if (nonHall !== model.indicators.omniNonHall) {
      changes.push({ model: model.name, key: 'omniNonHall', prev: model.indicators.omniNonHall, next: nonHall });
      log(`    omniNonHall: ${model.indicators.omniNonHall} -> ${nonHall} (derived)`);
      model.indicators.omniNonHall = nonHall;
    }

    // LiveBench is not exposed by the AA API. Always carried forward, always flagged.
    stale.push('liveBench');

    model.provenance.stale = stale;
    if (stale.length) staleReport.push({ model: model.name, fields: stale });

    for (const cand of findNewer(all, slot, api)) {
      newerReport.push({
        slot: slot.slot,
        current: `${model.name} (${api.artificial_analysis_intelligence_index?.toFixed(1)})`,
        candidate: `${cand.name} (${cand.artificial_analysis_intelligence_index?.toFixed(1)})`,
        slug: cand.slug,
      });
    }
  }

  data.meta.generatedAt = new Date().toISOString().slice(0, 10);
  data.meta.generatedBy = `refresh-model-data.mjs (AA index v${payload.intelligence_index_version})`;
  data.meta.intelligenceIndexVersion = String(payload.intelligence_index_version);

  log('\n' + '='.repeat(64));
  log(`${changes.length} value(s) changed.`);
  if (staleReport.length) {
    log('\nCarried forward, NOT refreshed this run:');
    for (const s of staleReport) log(`  ${s.model}: ${s.fields.join(', ')}`);
  }
  if (newerReport.length) {
    log('\nNewer models available (not swapped in — this is your call):');
    for (const n of newerReport) log(`  [${n.slot}] ${n.current}  ->  ${n.candidate}  slug=${n.slug}`);
    log('\nTo adopt one, edit its slot id/aaSlug in scripts/models.config.json,');
    log('add a description for the new id in src/lib/data.ts, then re-run.');
  } else {
    log('\nNo newer models found for any tracked lab.');
  }

  if (DRY_RUN) {
    log('\n--dry-run: nothing written.\n');
  } else {
    writeFileSync(DATA_PATH, JSON.stringify(data, null, 2) + '\n', 'utf8');
    log(`\nWrote ${DATA_PATH}\n`);
  }

  // Surface results to CI without re-running the script.
  if (process.env.GITHUB_OUTPUT) {
    const esc = (s) => s.replace(/\n/g, '%0A');
    writeFileSync(
      process.env.GITHUB_OUTPUT,
      `changed=${changes.length}\n` +
        `newer=${newerReport.length}\n` +
        `summary=${esc(
          [
            `${changes.length} value(s) updated.`,
            ...newerReport.map((n) => `NEWER: [${n.slot}] ${n.current} -> ${n.candidate} (slug: ${n.slug})`),
            ...staleReport.map((s) => `STALE: ${s.model}: ${s.fields.join(', ')}`),
          ].join('\n'),
        )}\n`,
      { flag: 'a' },
    );
  }
}

main().catch((err) => {
  console.error('\nRefresh failed:', err.message);
  console.error('No files were modified.\n');
  process.exit(1);
});

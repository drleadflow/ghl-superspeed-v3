#!/usr/bin/env node
/**
 * Build a single master .docx documenting every workflow in a dump dir
 * produced by scripts/dump_workflows.py + build_flow_map.py + dump_workflow_analytics.py.
 *
 * Inputs (under <out-dir>):
 *   _index.json        folders + workflow list (from dump_workflows.py)
 *   _flows.json        cross-workflow connections (from build_flow_map.py)
 *   _analytics.json    enrollment counts (from dump_workflow_analytics.py)
 *   workflows/<slug>__<id8>.json          raw workflow detail
 *   workflows/<slug>__<id8>.triggers.json raw triggers
 *   workflows/<slug>__<id8>.md            includes narrative summary
 *
 * Output:
 *   <out-dir>/<location-slug>-Workflow-Documentation.docx
 *
 * Usage:
 *   node scripts/build_workflow_docx.js <out-dir> [--label "Healthspan By Design"]
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, ExternalHyperlink,
  InternalHyperlink, Bookmark, TabStopType, TabStopPosition,
  TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageNumber, PageBreak, PageOrientation,
} = require(path.join("/Users/bleupreneur/.npm-global/lib/node_modules/docx"));

// ── CLI ──────────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
if (!args.length || args[0].startsWith("--")) {
  console.error("usage: build_workflow_docx.js <dump-dir> [--label \"Name\"]");
  process.exit(2);
}
const dumpDir = args[0];
const labelArg = args.indexOf("--label");
const accountLabel = labelArg >= 0 ? args[labelArg + 1] : "GHL Location";

// ── Data load ────────────────────────────────────────────────────────────────

const indexData = JSON.parse(fs.readFileSync(path.join(dumpDir, "_index.json"), "utf8"));
const flows = fs.existsSync(path.join(dumpDir, "_flows.json"))
  ? JSON.parse(fs.readFileSync(path.join(dumpDir, "_flows.json"), "utf8"))
  : { workflows: {}, id_to_name: {} };
const analytics = fs.existsSync(path.join(dumpDir, "_analytics.json"))
  ? JSON.parse(fs.readFileSync(path.join(dumpDir, "_analytics.json"), "utf8"))
  : null;

// Build path-by-id, slug-by-id
const folderById = Object.fromEntries(indexData.folders.map(f => [f.id, f]));
const pathById = {};
for (const w of indexData.workflows) {
  pathById[w.id] = (w.path || []).join(" / ") || "(root)";
}
const slugOf = (name) =>
  (name || "").replace(/[^a-zA-Z0-9._-]+/g, "-").replace(/^-+|-+$/g, "").toLowerCase().slice(0, 60) || "untitled";

function workflowFilesFor(wf) {
  const slug = slugOf(wf.name);
  const id8 = wf.id.slice(0, 8);
  return {
    detail: path.join(dumpDir, "workflows", `${slug}__${id8}.json`),
    triggers: path.join(dumpDir, "workflows", `${slug}__${id8}.triggers.json`),
    md: path.join(dumpDir, "workflows", `${slug}__${id8}.md`),
  };
}

// ── Helpers ──────────────────────────────────────────────────────────────────

const FONT = "Calibri";          // wide native availability + condenses to fewer pages
const MONO = "Consolas";
const DXA_INCH = 1440;
const PAGE_W = 12240;            // US Letter
const PAGE_H = 15840;
const MARGIN = 1080;             // 0.75 inch
const CONTENT_W = PAGE_W - 2 * MARGIN; // 10080 DXA

const COLOR = {
  heading: "1F3864",
  subhead: "2E5496",
  muted: "595959",
  tableHeader: "1F3864",
  tableHeaderText: "FFFFFF",
  tableAltRow: "F2F2F2",
  rule: "BFBFBF",
  codeBg: "F4F4F4",
};

const border = (color = COLOR.rule) => ({ style: BorderStyle.SINGLE, size: 4, color });
const allBorders = (color = COLOR.rule) => ({
  top: border(color), bottom: border(color), left: border(color), right: border(color),
});
const noBorders = {
  top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
};

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { before: opts.before || 0, after: opts.after || 80 },
    ...(opts.heading ? { heading: opts.heading } : {}),
    ...(opts.pageBreakBefore ? { pageBreakBefore: true } : {}),
    ...(opts.numbering ? { numbering: opts.numbering } : {}),
    children: [
      new TextRun({
        text,
        bold: opts.bold,
        italics: opts.italics,
        color: opts.color,
        size: opts.size,
        font: opts.font || FONT,
      }),
    ],
  });
}

function ps(children, opts = {}) {
  return new Paragraph({
    spacing: { before: opts.before || 0, after: opts.after || 80 },
    ...(opts.pageBreakBefore ? { pageBreakBefore: true } : {}),
    children: children,
  });
}

function bulletItem(text, opts = {}) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 0, after: 40 },
    children: [
      new TextRun({
        text,
        bold: opts.bold,
        italics: opts.italics,
        font: opts.font || FONT,
        color: opts.color,
        size: opts.size,
      }),
    ],
  });
}

function bulletRuns(runs) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 0, after: 40 },
    children: runs,
  });
}

function codeLines(text, maxLines = 40) {
  if (!text) return [p("(empty)", { italics: true, color: COLOR.muted, size: 18 })];
  const lines = String(text).split(/\r?\n/);
  const truncated = lines.length > maxLines;
  const shown = lines.slice(0, maxLines);
  if (truncated) shown.push(`… [truncated ${lines.length - maxLines} more lines]`);
  return shown.map(line =>
    new Paragraph({
      spacing: { before: 0, after: 0 },
      shading: { fill: COLOR.codeBg, type: ShadingType.CLEAR },
      children: [new TextRun({
        text: line || " ",
        font: MONO,
        size: 18,
      })],
    })
  );
}

function stripHtml(html) {
  if (!html) return "";
  let s = String(html);
  s = s.replace(/<(style|script)\b[^>]*>[\s\S]*?<\/\1>/gi, "");
  s = s.replace(/<\s*br\s*\/?\s*>/gi, "\n");
  s = s.replace(/<\s*\/p\s*>/gi, "\n");
  s = s.replace(/<[^>]+>/g, "");
  s = s.replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "<")
       .replace(/&gt;/g, ">").replace(/&quot;/g, "\"").replace(/&#39;/g, "'");
  s = s.replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n");
  return s.trim();
}

function extractSummary(mdPath) {
  if (!fs.existsSync(mdPath)) return null;
  const md = fs.readFileSync(mdPath, "utf8");
  const m = md.match(/## Summary\s*\n([\s\S]*?)(?=\n## )/);
  if (!m) return null;
  return m[1].trim();
}

// ── Tables ───────────────────────────────────────────────────────────────────

function headerCell(text, width) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders: allBorders(),
    shading: { fill: COLOR.tableHeader, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      children: [new TextRun({ text, bold: true, color: COLOR.tableHeaderText, font: FONT, size: 20 })],
    })],
  });
}

function bodyCell(text, width, opts = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders: allBorders(),
    shading: opts.alt ? { fill: COLOR.tableAltRow, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: opts.right ? AlignmentType.RIGHT : AlignmentType.LEFT,
      children: [new TextRun({
        text: text == null ? "" : String(text),
        font: opts.mono ? MONO : FONT,
        size: opts.size || 20,
        bold: opts.bold,
        italics: opts.italics,
        color: opts.color,
      })],
    })],
  });
}

function metaTable(rows) {
  // Two-column key/value table. Label col 2400 DXA, value col fills rest.
  const labelW = 2400;
  const valueW = CONTENT_W - labelW;
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [labelW, valueW],
    rows: rows.map(([k, v]) => new TableRow({
      children: [
        new TableCell({
          width: { size: labelW, type: WidthType.DXA },
          borders: allBorders(),
          shading: { fill: COLOR.tableAltRow, type: ShadingType.CLEAR },
          margins: { top: 60, bottom: 60, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: k, bold: true, font: FONT, size: 20 })] })],
        }),
        new TableCell({
          width: { size: valueW, type: WidthType.DXA },
          borders: allBorders(),
          margins: { top: 60, bottom: 60, left: 120, right: 120 },
          children: Array.isArray(v) ? v : [
            new Paragraph({ children: [new TextRun({ text: v == null ? "" : String(v), font: FONT, size: 20 })] })
          ],
        }),
      ],
    })),
  });
}

// ── Step renderer ────────────────────────────────────────────────────────────

const STEP_LABEL = {
  email: "Send Email",
  sms: "Send SMS",
  wait: "Wait",
  if_else: "If / Else",
  add_contact_tag: "Add Tag",
  remove_contact_tag: "Remove Tag",
  internal_notification: "Internal Notification",
  webhook: "Webhook",
  goto: "Go To Step",
  add_to_workflow: "Add to Workflow",
  remove_from_workflow: "Remove from Workflow",
  create_opportunity: "Create / Update Opportunity",
  google_sheets: "Google Sheets",
  math_operation: "Math Operation",
  event_start_date: "Event Start Date",
  update_contact_field: "Update Contact Field",
  update_appointment_status: "Update Appointment Status",
  assign_user: "Assign User",
  appointment_booking: "Appointment Booking",
  contact_engagement_score: "Contact Engagement Score",
  transition: "Transition",
  workflow_goal: "Workflow Goal",
  "instagram-dm": "Instagram DM",
  ig_interactive_messenger: "Instagram Interactive Messenger",
  respond_on_comment: "Respond on IG Comment",
};

function renderStep(t, idx) {
  const type = t.type || "?";
  const name = t.name || "(unnamed)";
  const label = STEP_LABEL[type] || type;
  const attrs = t.attributes || {};
  const children = [];

  // Step header
  children.push(new Paragraph({
    spacing: { before: 160, after: 60 },
    children: [
      new TextRun({ text: `Step ${idx + 1}  ·  `, font: FONT, size: 22, color: COLOR.muted }),
      new TextRun({ text: label, font: FONT, size: 22, bold: true, color: COLOR.subhead }),
      new TextRun({ text: `  ·  ${name}`, font: FONT, size: 22 }),
    ],
  }));

  if (type === "email") {
    const subject = attrs.subject || "(no subject)";
    const fromName = attrs.fromName || attrs.from_name || "";
    const fromEmail = attrs.fromEmail || attrs.from_email || "";
    const html = attrs.html || attrs.body || "";
    const templateId = attrs.template_id || attrs.templateId;
    const templatesource = attrs.templatesource || attrs.templateSource;
    children.push(metaTable([
      ["From", `${fromName}${fromName && fromEmail ? " " : ""}${fromEmail ? "<" + fromEmail + ">" : ""}`],
      ["Subject", subject],
      ...(templatesource ? [["Template source", templatesource]] : []),
      ...(templateId ? [["Template ID", templateId]] : []),
    ]));
    if (html) {
      children.push(p("Body (text):", { bold: true, before: 80, after: 40, size: 20 }));
      children.push(...codeLines(stripHtml(html), 60));
    } else if (templateId) {
      children.push(p("Body lives in GHL email-builder template (HTML not inlined in workflow JSON).",
                      { italics: true, color: COLOR.muted, size: 18, before: 80 }));
    }
  } else if (type === "sms") {
    const msg = attrs.message || attrs.body || "";
    children.push(p("Message:", { bold: true, before: 40, after: 40, size: 20 }));
    children.push(...codeLines(msg, 30));
    if (attrs.attachments && attrs.attachments.length) {
      children.push(p(`Attachments: ${JSON.stringify(attrs.attachments)}`, { size: 18, color: COLOR.muted }));
    }
  } else if (type === "internal_notification") {
    const channel = attrs.type || "?";
    const sub = attrs[channel] || {};
    const recipient = sub.to || sub.selectedUser || sub.userType || "?";
    const subject = sub.subject || "";
    const body = sub.body || sub.html || "";
    children.push(metaTable([
      ["Channel", channel],
      ["Recipient", JSON.stringify(recipient)],
      ...(sub.userType ? [["User type", sub.userType]] : []),
      ...(subject ? [["Subject", subject]] : []),
    ]));
    if (body) {
      children.push(p("Body:", { bold: true, before: 40, after: 40, size: 20 }));
      children.push(...codeLines(stripHtml(body), 20));
    }
  } else if (type === "wait") {
    let line = "wait (no attributes)";
    if (attrs.unit && attrs.amount != null) line = `Wait ${attrs.amount} ${attrs.unit}`;
    else if (attrs.waitDateTime) line = `Wait until ${attrs.waitDateTime}`;
    else line = "Wait: " + JSON.stringify(attrs).slice(0, 200);
    children.push(p(line, { size: 20 }));
  } else if (type === "add_contact_tag" || type === "remove_contact_tag") {
    const tags = (attrs.tags || []).join(", ");
    children.push(p(`Tags: ${tags || "(none)"}`, { size: 20 }));
  } else if (type === "if_else") {
    if (attrs.operator) children.push(p(`Operator: ${attrs.operator}`, { size: 20 }));
    for (const b of (attrs.branches || [])) {
      const segDescs = [];
      for (const seg of (b.segments || [])) {
        for (const c of (seg.conditions || [])) {
          segDescs.push(`${c.conditionType || "?"}:${c.conditionSubType || ""} `
                       + `${c.conditionOperator || ""} `
                       + `${JSON.stringify(c.conditionValue) || ""}`);
        }
      }
      children.push(bulletItem(`Branch "${b.name || "?"}": `
                               + (segDescs.length ? segDescs.join("; ") : "(no segments)"),
                               { size: 20 }));
    }
  } else if (type === "goto") {
    const target = attrs.targetStepId || attrs.targetStep || attrs.target || "?";
    children.push(p(`Goto step: ${target}`, { size: 20 }));
  } else if (type === "webhook") {
    const url = attrs.url || "?";
    const method = attrs.method || "POST";
    children.push(p(`${method} ${url}`, { size: 20, font: MONO }));
    if (attrs.data) {
      children.push(p("Payload:", { bold: true, before: 40, after: 40, size: 20 }));
      children.push(...codeLines(JSON.stringify(attrs.data, null, 2), 30));
    }
  } else if (type === "add_to_workflow" || type === "remove_from_workflow") {
    const v = attrs.workflow_id || attrs.workflowId;
    children.push(p(`Target workflow id(s): ${JSON.stringify(v)}`, { size: 20, font: MONO }));
  } else if (type === "create_opportunity") {
    children.push(metaTable([
      ["Pipeline", attrs.pipeline_id || ""],
      ["Stage", attrs.pipeline_stage_id || ""],
      ["Status", attrs.opportunity_status || ""],
      ["Name", attrs.opportunity_name || ""],
      ...(attrs.monetary_value ? [["Value", String(attrs.monetary_value)]] : []),
    ]));
  } else {
    // Generic dump
    children.push(p("Attributes:", { bold: true, before: 40, after: 40, size: 20 }));
    children.push(...codeLines(JSON.stringify(attrs, null, 2), 20));
  }

  return children;
}

// ── Trigger renderer ─────────────────────────────────────────────────────────

function renderTriggers(triggers) {
  const out = [];
  if (!triggers || triggers.length === 0) {
    out.push(p("No triggers found — this workflow is invoked by add_to_workflow, "
              + "manual run, or legacy tag trigger.",
              { italics: true, color: COLOR.muted, size: 20 }));
    return out;
  }
  for (const trig of triggers) {
    out.push(p(`Trigger: ${trig.type || "?"}${trig.name ? "  ·  " + trig.name : ""}`,
              { bold: true, color: COLOR.subhead, size: 22, before: 60, after: 60 }));
    const conds = trig.conditions || trig.filters || [];
    for (const c of conds) {
      const field = c.field || c.conditionType || "?";
      const op = c.operator || c.conditionOperator || "";
      const val = c.value != null ? c.value : c.conditionValue;
      const title = c.title;
      let line = `${field} ${op} ${JSON.stringify(val)}`;
      if (title) line += `  (${title})`;
      out.push(bulletItem(line, { size: 20 }));
    }
  }
  return out;
}

// ── Workflow section ─────────────────────────────────────────────────────────

function renderWorkflowSection(wf, isFirst) {
  const files = workflowFilesFor(wf);
  if (!fs.existsSync(files.detail)) {
    return [p(`(workflow detail missing for ${wf.name})`, { italics: true })];
  }
  const detail = JSON.parse(fs.readFileSync(files.detail, "utf8"));
  const triggers = fs.existsSync(files.triggers)
    ? JSON.parse(fs.readFileSync(files.triggers, "utf8")) : [];
  const summary = extractSummary(files.md);
  const flowEntry = flows.workflows ? flows.workflows[wf.id] : null;
  const stats = analytics && analytics.workflows ? analytics.workflows[wf.id] : null;

  const tmpls = (detail.workflowData && detail.workflowData.templates) || [];
  const out = [];

  // H2: workflow name + bookmark
  out.push(new Paragraph({
    heading: HeadingLevel.HEADING_2,
    pageBreakBefore: !isFirst,
    spacing: { before: 0, after: 120 },
    children: [new Bookmark({
      id: "wf-" + wf.id,
      children: [new TextRun({ text: wf.name || "(unnamed)", font: FONT })],
    })],
  }));

  // Metadata + counts
  out.push(metaTable([
    ["Workflow ID", [new Paragraph({ children: [new TextRun({ text: wf.id, font: MONO, size: 18 })] })]],
    ["Status", wf.status || "?"],
    ["Folder", pathById[wf.id] || "(root)"],
    ["Created", wf.createdAt || "?"],
    ["Last updated", wf.updatedAt || "?"],
    ["Enrollments (lifetime)", stats ? String(stats.total) : "n/a"],
    ["Completed", stats ? String(stats.finished) : "n/a"],
    ["Active now", stats ? String(stats.active) : "n/a"],
    ["Builder URL", [new Paragraph({ children: [new ExternalHyperlink({
      children: [new TextRun({ text: "Open in GHL", style: "Hyperlink", font: FONT, size: 20 })],
      link: `https://app.gohighlevel.com/location/${detail.locationId || indexData.locationId}/workflow/${wf.id}`,
    })] })]],
  ]));

  // Summary
  if (summary) {
    out.push(p("Summary", { heading: HeadingLevel.HEADING_3, before: 200, after: 60 }));
    // Render the summary markdown as paragraphs. Keep simple — split on lines,
    // bold the **labels:**, render `code` inline.
    for (const line of summary.split("\n")) {
      if (!line.trim()) continue;
      const isBullet = /^\s*-\s+/.test(line);
      const text = line.replace(/^\s*-\s+/, "");
      const runs = renderInlineMd(text);
      if (isBullet) {
        out.push(bulletRuns(runs));
      } else {
        out.push(new Paragraph({ spacing: { before: 0, after: 60 }, children: runs }));
      }
    }
  }

  // Connections
  if (flowEntry && (
    (flowEntry.inbound && (flowEntry.inbound.called_by.length || flowEntry.inbound.triggered_by_tag_adders.length))
    || (flowEntry.outbound && (flowEntry.outbound.calls_workflows.length || flowEntry.outbound.adds_tags.length || flowEntry.outbound.removes_tags.length))
  )) {
    out.push(p("Connections", { heading: HeadingLevel.HEADING_3, before: 180, after: 60 }));
    const idToName = (id) => (flows.id_to_name && flows.id_to_name[id]) || id;
    for (const caller of (flowEntry.inbound.called_by || [])) {
      out.push(bulletItem(`Called by: ${idToName(caller)}`, { size: 20 }));
    }
    for (const t of (flowEntry.inbound.triggered_by_tag_adders || [])) {
      out.push(bulletItem(`Tag handoff: ${idToName(t.workflow_id)} adds "${t.via_tag}" → fires this workflow`, { size: 20 }));
    }
    for (const target of (flowEntry.outbound.calls_workflows || [])) {
      out.push(bulletItem(`Calls: ${idToName(target)}`, { size: 20 }));
    }
    for (const target of (flowEntry.outbound.removes_workflows || [])) {
      out.push(bulletItem(`Removes from: ${idToName(target)}`, { size: 20 }));
    }
    if (flowEntry.outbound.adds_tags.length) {
      out.push(bulletItem(`Adds tags: ${flowEntry.outbound.adds_tags.join(", ")}`, { size: 20 }));
    }
    if (flowEntry.outbound.removes_tags.length) {
      out.push(bulletItem(`Removes tags: ${flowEntry.outbound.removes_tags.join(", ")}`, { size: 20 }));
    }
  }

  // Triggers
  out.push(p("Triggers", { heading: HeadingLevel.HEADING_3, before: 200, after: 60 }));
  out.push(...renderTriggers(triggers));

  // Steps
  out.push(p(`Action steps (${tmpls.length})`, { heading: HeadingLevel.HEADING_3, before: 200, after: 60 }));
  if (tmpls.length === 0) {
    out.push(p("No action steps in this workflow.", { italics: true, color: COLOR.muted, size: 20 }));
  } else {
    for (let i = 0; i < tmpls.length; i++) {
      out.push(...renderStep(tmpls[i], i));
    }
  }

  return out;
}

// ── Tiny inline-markdown renderer ────────────────────────────────────────────

function renderInlineMd(text) {
  // Recognize **bold**, `code`, and plain text. No nesting.
  const runs = [];
  const re = /(\*\*([^*]+)\*\*)|(`([^`]+)`)/g;
  let last = 0, m;
  while ((m = re.exec(text)) != null) {
    if (m.index > last) runs.push(new TextRun({ text: text.slice(last, m.index), font: FONT, size: 20 }));
    if (m[1]) runs.push(new TextRun({ text: m[2], bold: true, font: FONT, size: 20 }));
    else if (m[3]) runs.push(new TextRun({ text: m[4], font: MONO, size: 18 }));
    last = m.index + m[0].length;
  }
  if (last < text.length) runs.push(new TextRun({ text: text.slice(last), font: FONT, size: 20 }));
  if (runs.length === 0) runs.push(new TextRun({ text, font: FONT, size: 20 }));
  return runs;
}

// ── Front matter ─────────────────────────────────────────────────────────────

function buildFrontMatter() {
  const out = [];
  // Title block
  out.push(new Paragraph({
    spacing: { before: 1600, after: 240 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: accountLabel, bold: true, color: COLOR.heading, size: 48, font: FONT })],
  }));
  out.push(new Paragraph({
    spacing: { before: 0, after: 240 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Workflow Documentation", color: COLOR.subhead, size: 36, font: FONT })],
  }));
  out.push(new Paragraph({
    spacing: { before: 0, after: 240 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: `Location ${indexData.locationId}  ·  Generated ${new Date().toISOString().slice(0, 10)}`,
      color: COLOR.muted, size: 22, font: FONT,
    })],
  }));
  out.push(new Paragraph({ children: [new PageBreak()] }));

  // Totals
  if (analytics) {
    const t = analytics.totals;
    out.push(p("Account totals", { heading: HeadingLevel.HEADING_1, before: 0, after: 200 }));
    out.push(metaTable([
      ["Workflows", String(t.workflow_count)],
      ["Lifetime enrollments", t.total_enrollments.toLocaleString()],
      ["Completed", t.total_finished.toLocaleString()],
      ["Currently active", t.total_active.toLocaleString()],
      ["Workflows with traffic", `${t.workflows_with_traffic} / ${t.workflow_count}`],
      ["Workflows with zero enrollment", String(t.workflows_zero_traffic)],
      ["Location-wide errors awaiting review", t.error_notifications == null ? "n/a" : String(t.error_notifications)],
    ]));

    // Top 20 table
    out.push(p("Top 20 workflows by lifetime enrollment", { heading: HeadingLevel.HEADING_2, before: 240, after: 120 }));
    const ranked = Object.values(analytics.workflows).sort((a, b) => b.total - a.total).slice(0, 20);
    const widths = [Math.round(CONTENT_W * 0.06), Math.round(CONTENT_W * 0.54),
                    Math.round(CONTENT_W * 0.12), Math.round(CONTENT_W * 0.10),
                    Math.round(CONTENT_W * 0.10), Math.round(CONTENT_W * 0.08)];
    // Adjust the last to make the sum exact
    widths[widths.length - 1] = CONTENT_W - widths.slice(0, -1).reduce((a, b) => a + b, 0);
    out.push(new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: widths,
      rows: [
        new TableRow({ tableHeader: true, children: [
          headerCell("#", widths[0]),
          headerCell("Workflow", widths[1]),
          headerCell("Status", widths[2]),
          headerCell("Total", widths[3]),
          headerCell("Done", widths[4]),
          headerCell("Active", widths[5]),
        ]}),
        ...ranked.map((w, i) => {
          const idxW = (indexData.workflows.find(x => x.id === w.id) || {});
          return new TableRow({
            children: [
              bodyCell(String(i + 1), widths[0], { alt: i % 2 === 1, right: true }),
              bodyCell(w.name, widths[1], { alt: i % 2 === 1 }),
              bodyCell(idxW.status || "?", widths[2], { alt: i % 2 === 1, mono: true, size: 18 }),
              bodyCell(w.total.toLocaleString(), widths[3], { alt: i % 2 === 1, right: true }),
              bodyCell(w.finished.toLocaleString(), widths[4], { alt: i % 2 === 1, right: true }),
              bodyCell(w.active.toLocaleString(), widths[5], { alt: i % 2 === 1, right: true, bold: w.active > 0 }),
            ],
          });
        }),
      ],
    }));
  }

  // Folder TOC w/ internal links
  out.push(p("Workflow index", { heading: HeadingLevel.HEADING_1, before: 360, after: 200, pageBreakBefore: true }));
  const byFolder = {};
  for (const w of indexData.workflows) {
    const key = (w.path || []).join(" / ") || "(root)";
    (byFolder[key] = byFolder[key] || []).push(w);
  }
  for (const fname of Object.keys(byFolder).sort()) {
    out.push(p(fname, { heading: HeadingLevel.HEADING_3, before: 160, after: 60 }));
    for (const w of byFolder[fname].sort((a, b) => (a.name || "").localeCompare(b.name || ""))) {
      const stats = analytics && analytics.workflows ? analytics.workflows[w.id] : null;
      const tail = stats ? `  —  ${stats.total} enrolled` : "";
      out.push(new Paragraph({
        spacing: { before: 0, after: 20 },
        children: [
          new InternalHyperlink({
            children: [new TextRun({ text: w.name, style: "Hyperlink", font: FONT, size: 20 })],
            anchor: "wf-" + w.id,
          }),
          new TextRun({ text: ` · ${w.status || "?"}${tail}`, color: COLOR.muted, font: FONT, size: 18 }),
        ],
      }));
    }
  }
  return out;
}

// ── Build document ───────────────────────────────────────────────────────────

const docChildren = [];
docChildren.push(...buildFrontMatter());

// All workflows, in folder order
const sortedWfs = [...indexData.workflows].sort((a, b) => {
  const pa = (a.path || []).join("/");
  const pb = (b.path || []).join("/");
  if (pa !== pb) return pa.localeCompare(pb);
  return (a.name || "").localeCompare(b.name || "");
});

let firstWf = true;
for (const wf of sortedWfs) {
  docChildren.push(...renderWorkflowSection(wf, firstWf));
  firstWf = false;
  process.stderr.write(`[docx] ${wf.name}\n`);
}

const doc = new Document({
  creator: "GHL Workflow Dumper",
  title: `${accountLabel} — Workflow Documentation`,
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, color: COLOR.heading, font: FONT },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, color: COLOR.heading, font: FONT },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: COLOR.subhead, font: FONT },
        paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 2 } },
      { id: "Hyperlink", name: "Hyperlink", basedOn: "Normal",
        run: { color: "2E5496", underline: { type: "single" } } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.LEFT,
          spacing: { after: 60 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: COLOR.heading, space: 2 } },
          children: [new TextRun({ text: `${accountLabel} — Workflow Documentation`, color: COLOR.muted, size: 18, font: FONT })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
          children: [
            new TextRun({ text: `Generated ${new Date().toISOString().slice(0, 10)}`, color: COLOR.muted, size: 18, font: FONT }),
            new TextRun({ text: "\tPage " }),
            new TextRun({ children: [PageNumber.CURRENT] }),
            new TextRun({ text: " of " }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES] }),
          ],
        })],
      }),
    },
    children: docChildren,
  }],
});

const outPath = path.join(dumpDir, `${slugOf(accountLabel)}-Workflow-Documentation.docx`);
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  const kb = Math.round(buf.length / 1024);
  console.log(`[docx] wrote ${outPath} (${kb} KB)`);
}).catch(err => {
  console.error("[docx] build failed:", err);
  process.exit(1);
});

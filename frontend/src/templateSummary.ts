import type { ServiceTemplate, TemplateSummary } from "./types";

export function upsertTemplateSummary(
  templates: TemplateSummary[],
  template: ServiceTemplate
): TemplateSummary[] {
  const summary: TemplateSummary = {
    id: template.id,
    name: template.name,
    builtin: template.builtin,
    description: template.description,
    section_count: template.sections.length,
    media_asset_count: template.media_assets.length,
  };
  return templates.some((item) => item.id === summary.id)
    ? templates.map((item) => item.id === summary.id ? summary : item)
    : [...templates, summary];
}

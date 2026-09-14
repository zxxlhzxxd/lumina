import { useEffect, useRef, useState } from "react";
import { Button, Input, Modal, Select, Space } from "antd";
import { ImportOutlined } from "@ant-design/icons";
import { useTemplateImport } from "../hooks/useTemplateImport";
import type { ServiceTemplate, TemplateSummary } from "../types";

interface Props {
  open: boolean;
  templates: TemplateSummary[];
  onCancel: () => void;
  onCreate: (templateId: string, name: string) => Promise<void>;
  onTemplateImported: (template: ServiceTemplate) => void;
}

export function NewProjectModal({
  open,
  templates,
  onCancel,
  onCreate,
  onTemplateImported,
}: Props) {
  const [name, setName] = useState("主日崇拜");
  const [templateId, setTemplateId] = useState("");
  const [creating, setCreating] = useState(false);
  const createPending = useRef(false);
  const { importing, importTemplate } = useTemplateImport();
  const busy = importing || creating;

  useEffect(() => {
    if (open && !templates.some((template) => template.id === templateId)) {
      setTemplateId(templates[0]?.id ?? "");
    }
  }, [open, templates, templateId]);

  const handleImport = async () => {
    if (busy || createPending.current) return;
    const template = await importTemplate();
    if (!template) return;
    onTemplateImported(template);
    setTemplateId(template.id);
  };

  const handleCreate = async () => {
    if (busy || createPending.current) return;
    createPending.current = true;
    setCreating(true);
    try {
      await onCreate(templateId, name);
    } finally {
      createPending.current = false;
      setCreating(false);
    }
  };

  return (
    <Modal
      title="新建礼拜工程"
      open={open}
      onCancel={() => {
        if (!busy) onCancel();
      }}
      onOk={handleCreate}
      okText="创建"
      cancelText="取消"
      confirmLoading={creating}
      okButtonProps={{ disabled: busy }}
      cancelButtonProps={{ disabled: busy }}
      closable={!busy}
      maskClosable={!busy}
      keyboard={!busy}
    >
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        <div>
          <label htmlFor="new-project-name" style={{ display: "block", marginBottom: 6 }}>
            工程名称
          </label>
          <Input
            id="new-project-name"
            value={name}
            disabled={busy}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="new-project-template" style={{ display: "block", marginBottom: 6 }}>
            流程模板
          </label>
          <div style={{ display: "flex", gap: 8 }}>
            <Select
              id="new-project-template"
              style={{ flex: 1, minWidth: 0 }}
              value={templateId || undefined}
              disabled={busy}
              onChange={setTemplateId}
              options={templates.map((template) => ({
                label: `${template.name}（${template.section_count} 段）`,
                value: template.id,
              }))}
            />
            <Button
              icon={<ImportOutlined />}
              loading={importing}
              disabled={busy}
              onClick={handleImport}
            >
              导入模板
            </Button>
          </div>
        </div>
      </Space>
    </Modal>
  );
}

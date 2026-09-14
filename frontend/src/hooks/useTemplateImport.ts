import { useCallback, useRef, useState } from "react";
import { App as AntApp } from "antd";
import { api, pickTemplateImportPath } from "../api";
import type { ServiceTemplate } from "../types";

export function useTemplateImport() {
  const { message } = AntApp.useApp();
  const [importing, setImporting] = useState(false);
  const pending = useRef(false);

  const importTemplate = useCallback(async (): Promise<ServiceTemplate | null> => {
    if (pending.current) return null;
    pending.current = true;
    setImporting(true);
    try {
      const path = await pickTemplateImportPath();
      if (!path) return null;
      const template = await api.importTemplate(path);
      message.success("已导入模板");
      return template;
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : "导入失败");
      return null;
    } finally {
      pending.current = false;
      setImporting(false);
    }
  }, [message]);

  return { importing, importTemplate };
}

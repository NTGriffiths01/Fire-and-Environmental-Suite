import { useQuery } from "@tanstack/react-query";
import Form from "@rjsf/core";
import { JSONSchema7 } from "json-schema";
import toast from "react-hot-toast";

interface Props {
  templateId: string;
  inspectionId?: string;
}

export default function DynamicInspectionForm({ templateId, inspectionId }: Props) {
  const token = localStorage.getItem("token");

  // Fetch template schema
  const { data: template } = useQuery(["template", templateId], async () => {
    const r = await fetch(`/api/templates/${templateId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return r.json();
  });

  // Fetch existing inspection (edit mode)
  const { data: inspection } = useQuery(
    ["inspection", inspectionId],
    async () => {
      if (!inspectionId) return undefined;
      const r = await fetch(`/api/inspections/${inspectionId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return r.json();
    },
    { enabled: !!inspectionId }
  );

  if (!template) return <p>Loading…</p>;

  const handleSubmit = async ({ formData }: { formData: any }) => {
    const endpoint = inspectionId ? `/api/inspections/${inspectionId}` : "/api/inspections";
    const method = inspectionId ? "PUT" : "POST";
    const res = await fetch(endpoint, {
      method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ templateId, payload: formData }),
    });
    res.ok ? toast.success("Inspection saved") : toast.error("Error saving inspection");
  };

  return (
    <div className="bg-white p-4 rounded shadow">
      <Form
        schema={template.schema as JSONSchema7}
        formData={inspection?.payload}
        onSubmit={handleSubmit}
        liveValidate
      />
    </div>
  );
}
import React from "react";
import { useQuery } from "@tanstack/react-query";
import Form from "@rjsf/core";
import validator from "@rjsf/validator-ajv8";
import { RJSFSchema } from "@rjsf/utils";
import toast from "react-hot-toast";

interface Props {
  templateId: string;
  inspectionId?: string;
  onSuccess?: () => void;
}

export default function DynamicInspectionForm({ templateId, inspectionId, onSuccess }: Props) {
  const token = localStorage.getItem("token");

  // Fetch template schema
  const { data: template, isLoading: templateLoading } = useQuery({
    queryKey: ["template", templateId],
    queryFn: async () => {
      const response = await fetch(`/api/v2/templates/${templateId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error("Failed to fetch template");
      }
      return response.json();
    },
    enabled: !!templateId,
  });

  // Fetch existing inspection (edit mode)
  const { data: inspection, isLoading: inspectionLoading } = useQuery({
    queryKey: ["inspection", inspectionId],
    queryFn: async () => {
      if (!inspectionId) return undefined;
      const response = await fetch(`/api/v2/inspections/${inspectionId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error("Failed to fetch inspection");
      }
      return response.json();
    },
    enabled: !!inspectionId,
  });

  if (templateLoading || inspectionLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-900"></div>
        <span className="ml-2 text-gray-600">Loading...</span>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="text-center p-8 text-red-600">
        <p>Template not found or failed to load</p>
      </div>
    );
  }

  const handleSubmit = async ({ formData }: { formData: any }) => {
    try {
      const endpoint = inspectionId ? `/api/v2/inspections/${inspectionId}` : "/api/v2/inspections";
      const method = inspectionId ? "PUT" : "POST";
      
      const requestData = inspectionId 
        ? { payload: formData }
        : { 
            template_id: templateId,
            facility: "Default Facility", // This could be made configurable
            payload: formData 
          };

      const response = await fetch(endpoint, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        toast.success(inspectionId ? "Inspection updated successfully" : "Inspection created successfully");
        if (onSuccess) onSuccess();
      } else {
        const errorData = await response.json();
        toast.error(`Error: ${errorData.detail || "Failed to save inspection"}`);
      }
    } catch (error) {
      toast.error("Network error occurred");
      console.error("Error saving inspection:", error);
    }
  };

  const handleError = (errors: any) => {
    toast.error("Please fix the form errors");
    console.error("Form validation errors:", errors);
  };

  // Ensure the schema is properly formatted for RJSF
  const formSchema: RJSFSchema = template.schema || {
    type: "object",
    properties: {},
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          {template.name || "Inspection Form"}
        </h2>
        <p className="text-gray-600">
          {inspectionId ? "Edit existing inspection" : "Create new inspection"}
        </p>
      </div>

      <Form
        schema={formSchema}
        validator={validator}
        formData={inspection?.payload || {}}
        onSubmit={handleSubmit}
        onError={handleError}
        liveValidate
        showErrorList
        uiSchema={{
          "ui:submitButtonOptions": {
            submitText: inspectionId ? "Update Inspection" : "Create Inspection",
            norender: false,
            props: {
              className: "bg-blue-900 hover:bg-blue-800 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-150",
            },
          },
        }}
      />
    </div>
  );
}
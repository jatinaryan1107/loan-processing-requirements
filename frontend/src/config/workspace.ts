import type { Role, View } from "../types";
import {
  FolderKanban,
  MessageSquareText,
  ListChecks,
  ShieldCheck,
  GitBranch,
  FileCheck2,
  Layers3,
} from "lucide-react";

export const roles: {
  id: Role;
  name: string;
  initials: string;
  description: string;
}[] = [
  {
    id: "ba",
    name: "Business Analyst",
    initials: "BA",
    description: "Gather, clarify and validate requirements",
  },
  {
    id: "compliance",
    name: "Compliance Officer",
    initials: "CO",
    description: "Review policy evidence and interpretations",
  },
  {
    id: "pm",
    name: "Project Manager",
    initials: "PM",
    description: "Choose a lifecycle and export deliverables",
  },
  {
    id: "developer",
    name: "Software Developer",
    initials: "SD",
    description: "Read approved requirements and workflows",
  },
];
export const navigation: {
  id: View;
  title: string;
  icon: typeof Layers3;
  caption: string;
}[] = [
  {
    id: "overview",
    title: "Overview",
    icon: FolderKanban,
    caption: "Your project at a glance",
  },
  {
    id: "gather",
    title: "Gather requirements",
    icon: MessageSquareText,
    caption: "Capture context. Keep the source.",
  },
  {
    id: "analyse",
    title: "Analyse & validate",
    icon: ListChecks,
    caption: "Turn intent into testable requirements",
  },
  {
    id: "compliance",
    title: "Compliance review",
    icon: ShieldCheck,
    caption: "Evidence before interpretation",
  },
  {
    id: "sdlc",
    title: "SDLC recommendation",
    icon: GitBranch,
    caption: "A lifecycle that fits your project",
  },
  {
    id: "export",
    title: "Documents & audit",
    icon: FileCheck2,
    caption: "From decisions to deliverables",
  },
];

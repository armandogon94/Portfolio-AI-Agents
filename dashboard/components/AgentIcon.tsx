import {
  BarChart3,
  BookOpen,
  Bot,
  ClipboardList,
  Edit3,
  FileCheck,
  FileText,
  Heart,
  Home,
  Lightbulb,
  LineChart,
  List,
  Megaphone,
  MessageSquare,
  Network,
  PenLine,
  Phone,
  Scale,
  Search,
  ShieldCheck,
  Target,
  TrendingUp,
  Type,
  UserSearch,
  Users,
  type LucideIcon,
} from "lucide-react";

const ROLE_ICONS: Record<string, LucideIcon> = {
  crew: Network,
  agent: Bot,

  // research_report
  researcher: Search,
  analyst: BarChart3,
  writer: PenLine,
  validator: ShieldCheck,

  // sales pack
  scorer: Target,
  report_writer: FileText,
  persona_researcher: UserSearch,
  copywriter_formal: Type,
  copywriter_casual: Type,
  copywriter_provocative: Type,
  tone_checker: Scale,

  // support & ops
  triage_manager: Users,
  kb_searcher: BookOpen,
  sentiment_analyst: Heart,
  response_writer: MessageSquare,
  attendee_researcher: Users,
  topic_researcher: Lightbulb,
  agenda_writer: ClipboardList,
  talking_points_writer: Megaphone,

  // content + RE
  outliner: List,
  editor: Edit3,
  seo_optimizer: TrendingUp,
  comps_gatherer: Home,
  market_analyst: LineChart,
  appraiser: Scale,

  // voice
  intake_agent: ClipboardList,
  caller_agent: Phone,
  summary_agent: FileCheck,
};

export function AgentIcon({
  role,
  className,
}: {
  role: string;
  className?: string;
}) {
  const Icon = ROLE_ICONS[role] ?? Bot;
  return <Icon className={className} aria-hidden />;
}

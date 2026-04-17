export interface BrainMeta {
    name: string;
    slug: string;
    source: string;
    atom_count: number;
    connection_count: number;
    cluster_count: number;
    topic_count: number;
    connection_types: Record<string, number>;
    last_updated: string;
    coverage: Record<string, number>;
    bio: string;
    possessive: string;
}
export interface AtomConnection {
    target_id: string;
    relationship: "supports" | "contradicts" | "extends" | "related" | "inspired_by";
    confidence: number;
}
export interface Atom {
    id: string;
    content: string;
    cluster: string;
    topics: string[];
    source_ref: string;
    source_date: string;
    confidence: number;
    confidence_tier: "high" | "medium" | "low";
    original_quote: string | null;
    implication: string | null;
    connections: AtomConnection[];
}
export interface TopLevelConnection {
    id: string;
    atom_id_1: string;
    atom_id_2: string;
    relationship: string;
    confidence: number;
}
export interface SynthesisPrinciple {
    title: string;
    desc: string;
}
export interface SynthesisPattern {
    name: string;
    desc: string;
}
export interface BiographyEntry {
    date: string;
    role: string;
    lesson: string;
}
export interface Synthesis {
    hero_tagline: string;
    hero_updated: string;
    first_principles: SynthesisPrinciple[];
    thinking_patterns: SynthesisPattern[];
    contrarian_positions: SynthesisPrinciple[];
    does_not_believe: SynthesisPrinciple[];
    would_not_say: SynthesisPrinciple[];
    biography: BiographyEntry[];
    skills: Array<{
        name: string;
        title: string;
        desc: string;
        example: string;
    }>;
}
export interface BrainData {
    brain: BrainMeta;
    atoms: Atom[];
    connections: TopLevelConnection[];
    topic_index: Record<string, string[]>;
    synthesis: Synthesis;
}
export interface BrainIndex {
    atomsById: Map<string, Atom>;
    atomsByTopic: Map<string, Atom[]>;
    atomsByCluster: Map<string, Atom[]>;
}
export interface IndexEntry {
    slug: string;
    name: string;
    source: string;
    atom_count: number;
    connection_count: number;
    status: string;
    pack_path: string;
}
export interface BrainsIndex {
    brains: IndexEntry[];
}

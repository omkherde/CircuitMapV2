import type { TraceEvent } from '../types';

export const alzheimersDemo: TraceEvent[] = [
  {
    type: 'agent_thought',
    content: "I'll begin by resolving the molecular target for Chaetocin, a natural product with reported epigenetic activity...",
    timestamp: Date.now(),
  },
  {
    type: 'tool_call',
    tool: 'resolve_target',
    input: { query: 'Chaetocin', query_type: 'name' },
    timestamp: Date.now(),
  },
  {
    type: 'tool_result',
    tool: 'resolve_target',
    summary: 'Target: SUV39H1 (histone methyltransferase) | Affinity: 0.8 µM (Ki) | Source: ChEMBL',
    timestamp: Date.now(),
  },
  {
    type: 'confidence_update',
    dimension: 'target_resolution',
    level: 'HIGH',
    rationale: 'SUV39H1 confirmed as primary target with Ki = 0.8 µM from ChEMBL bioactivity data. Well-characterized mechanism of action.',
    timestamp: Date.now(),
  },
  {
    type: 'agent_thought',
    content: "Now I'll retrieve the brain expression pattern for SUV39H1 from the Allen Human Brain Atlas...",
    timestamp: Date.now(),
  },
  {
    type: 'tool_call',
    tool: 'get_brain_expression',
    input: { gene_name: 'SUV39H1' },
    timestamp: Date.now(),
  },
  {
    type: 'brain_map',
    map_type: 'expression',
    image_url: '/placeholder-expression.svg',
    top_regions: [
      { region: 'hippocampus', percentile: 98 },
      { region: 'entorhinal cortex', percentile: 94 },
      { region: 'prefrontal cortex', percentile: 87 },
    ],
    timestamp: Date.now(),
  },
  {
    type: 'tool_result',
    tool: 'get_brain_expression',
    summary: 'SUV39H1 shows high expression in hippocampus (p98), entorhinal cortex (p94), prefrontal cortex (p87)',
    timestamp: Date.now(),
  },
  {
    type: 'agent_thought',
    content: "Next, I'll retrieve the disease-related atrophy pattern for Alzheimer's disease...",
    timestamp: Date.now(),
  },
  {
    type: 'tool_call',
    tool: 'get_disease_map',
    input: { indication: "Alzheimer's disease" },
    timestamp: Date.now(),
  },
  {
    type: 'brain_map',
    map_type: 'disease',
    image_url: '/placeholder-disease.svg',
    top_regions: [
      { region: 'hippocampus', value: 0.92 },
      { region: 'entorhinal cortex', value: 0.88 },
      { region: 'temporal lobe', value: 0.76 },
    ],
    timestamp: Date.now(),
  },
  {
    type: 'tool_result',
    tool: 'get_disease_map',
    summary: "Alzheimer's disease shows primary atrophy in hippocampus, entorhinal cortex, and temporal lobe",
    timestamp: Date.now(),
  },
  {
    type: 'agent_thought',
    content: "Computing the spatial correlation between target expression and disease anatomy...",
    timestamp: Date.now(),
  },
  {
    type: 'tool_call',
    tool: 'compute_overlap',
    input: { target_map: 'SUV39H1', disease_map: 'alzheimers' },
    timestamp: Date.now(),
  },
  {
    type: 'overlap_score',
    r: 0.61,
    percentile: 89,
    label: "SUV39H1 expression vs Alzheimer's disease anatomy",
    timestamp: Date.now(),
  },
  {
    type: 'confidence_update',
    dimension: 'circuit_alignment',
    level: 'HIGH',
    rationale: 'Strong spatial correlation (r=0.61, p89) between SUV39H1 expression and Alzheimer\'s atrophy pattern. Target is expressed in disease-relevant circuits.',
    timestamp: Date.now(),
  },
  {
    type: 'agent_thought',
    content: "Now searching the literature for evidence linking SUV39H1 to Alzheimer's pathophysiology...",
    timestamp: Date.now(),
  },
  {
    type: 'tool_call',
    tool: 'search_literature',
    input: { query: "SUV39H1 Alzheimer's disease epigenetics" },
    timestamp: Date.now(),
  },
  {
    type: 'tool_result',
    tool: 'search_literature',
    summary: 'Found 12 relevant publications. Key finding: SUV39H1 regulates H3K9 methylation linked to memory consolidation.',
    timestamp: Date.now(),
  },
  {
    type: 'confidence_update',
    dimension: 'literature_support',
    level: 'MODERATE',
    rationale: 'Moderate literature support. SUV39H1 implicated in memory processes via H3K9 methylation, but direct AD therapeutic evidence is limited.',
    timestamp: Date.now(),
  },
  {
    type: 'agent_thought',
    content: "Compiling the final validation report with all findings...",
    timestamp: Date.now(),
  },
  {
    type: 'report_ready',
    report_sections: {
      executive_summary: "Chaetocin, targeting SUV39H1 (Ki = 0.8 µM), shows promising circuit alignment with Alzheimer's disease pathology. The target is highly expressed in disease-affected regions including the hippocampus and entorhinal cortex, with a strong spatial correlation (r = 0.61, p89) to the disease atrophy pattern.",
      target_identification: "Primary target: SUV39H1 (histone-lysine N-methyltransferase)\nAffinity: Ki = 0.8 µM\nMechanism: Inhibits H3K9 trimethylation\nSource: ChEMBL bioactivity database",
      expression_analysis: "SUV39H1 shows enriched expression in limbic structures critical for memory:\n• Hippocampus: 98th percentile\n• Entorhinal cortex: 94th percentile\n• Prefrontal cortex: 87th percentile\n\nThis expression pattern aligns with regions involved in memory formation and early Alzheimer's pathology.",
      spatial_overlap: "Correlation coefficient: r = 0.61\nPercentile rank: 89th (compared to 1000 null permutations)\n\nThis indicates that SUV39H1 expression is significantly higher in brain regions most affected by Alzheimer's disease, suggesting the target may engage disease-relevant neural circuits.",
      circuit_interpretation: "The strong spatial overlap suggests Chaetocin could modulate epigenetic processes specifically in circuits affected by Alzheimer's. The hippocampal-entorhinal expression pattern is particularly relevant given these regions' role in episodic memory and their early vulnerability in AD progression.",
      off_target_risk: "Chaetocin's therapeutic case is limited by multi-target activity and chemistry liabilities:\n• HIF1A pathway modulation may alter adaptive hypoxia responses\n• EHMT2/G9a inhibition broadens chromatin effects beyond SUV39H1\n• The epidithiodiketopiperazine scaffold may contribute ROS-mediated toxicity",
      literature_context: "Recent studies support SUV39H1's role in cognitive function:\n• Graff et al. (2012): H3K9 methylation regulates memory consolidation\n• Peleg et al. (2010): Histone modifications altered in aging hippocampus\n• Day & Bhattacharya (2019): Epigenetic mechanisms in Alzheimer's disease\n\nHowever, direct therapeutic evidence for SUV39H1 inhibition in AD is limited.",
      confidence_assessment: "Target Resolution: HIGH - Well-characterized target with confirmed binding data\nCircuit Alignment: HIGH - Strong spatial correlation with disease pattern\nLiterature Support: MODERATE - Mechanistic rationale exists but clinical validation lacking",
      limitations: "• In vitro binding data may not reflect in vivo target engagement\n• Blood-brain barrier penetration of Chaetocin unknown\n• Off-target effects on related methyltransferases not fully characterized\n• Spatial correlation does not prove causal therapeutic mechanism",
      recommendations: "• ADAS-Cog13 or equivalent episodic memory endpoint\n• Hippocampal MRI volumetry\n• Default mode network connectivity\n• Peripheral H3K9 methylation pharmacodynamic readout",
      preclinical_validation: "1. Evaluate BBB penetration and CNS pharmacokinetics\n2. Assess selectivity against related HMT enzymes\n3. Test in preclinical AD models for cognitive endpoints\n4. Consider prodrug strategies if CNS exposure is limited",
    },
    timestamp: Date.now(),
  },
  {
    type: 'pdf_ready',
    pdf_url: '/api/report/demo_alzheimers/download',
    filename: 'circuitmap-chaetocin-alzheimers.pdf',
    timestamp: Date.now(),
  },
  {
    type: 'done',
    timestamp: Date.now(),
  },
];

export const schizophreniaDemo: TraceEvent[] = [
  {
    type: 'agent_thought',
    content: "Analyzing Tolcapone's target profile for schizophrenia — COMT inhibition in prefrontal dopamine circuits...",
    timestamp: Date.now(),
  },
  {
    type: 'tool_call',
    tool: 'resolve_target',
    input: { query: 'Tolcapone', query_type: 'name' },
    timestamp: Date.now(),
  },
  {
    type: 'tool_result',
    tool: 'resolve_target',
    summary: 'Target: COMT (Catechol-O-methyltransferase) | Ki ≈ 1-10 nM | Source: ChEMBL',
    timestamp: Date.now(),
  },
  {
    type: 'confidence_update',
    dimension: 'target_resolution',
    level: 'HIGH',
    rationale: 'COMT well-characterized; Val158Met polymorphism highly relevant to schizophrenia prefrontal dopamine.',
    timestamp: Date.now(),
  },
  {
    type: 'done',
    timestamp: Date.now(),
  },
];

export const depressionDemo: TraceEvent[] = [
  {
    type: 'agent_thought',
    content: "Investigating Vorinostat (HDAC inhibitor) for major depressive disorder — epigenetic mechanisms in hippocampus/amygdala...",
    timestamp: Date.now(),
  },
  {
    type: 'tool_call',
    tool: 'resolve_target',
    input: { query: 'Vorinostat', query_type: 'name' },
    timestamp: Date.now(),
  },
  {
    type: 'tool_result',
    tool: 'resolve_target',
    summary: 'Primary target: HDAC2 (Histone deacetylase 2) | IC50 ≈ 48 nM | Source: ChEMBL',
    timestamp: Date.now(),
  },
  {
    type: 'confidence_update',
    dimension: 'target_resolution',
    level: 'MODERATE',
    rationale: 'HDAC2 is primary target but Vorinostat is pan-HDAC; selectivity for HDAC1/2 vs others warrants investigation.',
    timestamp: Date.now(),
  },
  {
    type: 'done',
    timestamp: Date.now(),
  },
];

export const demoScenarios = {
  alzheimers: alzheimersDemo,
  schizophrenia: schizophreniaDemo,
  depression: depressionDemo,
};

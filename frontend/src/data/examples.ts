export interface ExampleBrief {
  label: string;
  brief: string;
  sampleImage?: string; // path under /sample-images/
}

export const EXAMPLE_BRIEFS: ExampleBrief[] = [
  {
    label: "Classic oval engagement ring",
    brief:
      "I need a custom 18K yellow-gold engagement ring with an oval center diamond, six small stones on each side, approximately a 1.5-carat center stone, and a slim band.",
  },
  {
    label: "White-gold halo ring (with photo)",
    brief:
      "An 18k white gold halo engagement ring with a round center diamond and small pave side stones around the halo.",
    sampleImage: "engagement_2carat_diamond.jpg",
  },
  {
    label: "Channel-set side stones (with photo)",
    brief:
      "A white gold engagement ring with a round center diamond and princess-cut channel-set side stones along the band.",
    sampleImage: "classic_diamond_engagement.jpg",
  },
  {
    label: "Yellow-gold solitaire, no side stones (with photo)",
    brief: "An 18k yellow gold solitaire ring with a round diamond center stone and no side stones.",
    sampleImage: "diamond_ring_top_down.jpg",
  },
  {
    label: "Silver citrine ring (with photo)",
    brief: "A sterling silver ring with a large oval citrine centerpiece and an open filigree band, no side stones.",
    sampleImage: "citrine_silver_ring.jpg",
  },
  {
    label: "Vague brief (tests graceful uncertainty)",
    brief: "Something elegant for my partner, nothing too flashy.",
  },
  {
    label: "Implausible carat (tests plausibility flag)",
    brief: "I want an 18k gold ring with a 50 carat round diamond center stone.",
  },
];

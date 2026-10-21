# Industrial Zone asset pack

The Normal-difficulty renderer reads the supplied Industrial Zone pack from this folder. Source pixel art is preserved at its native 32px tile scale; background layers are cached at an integer 2x nearest-neighbour scale for the 960x540 game viewport.

- `tiles/`: 81 individual `IndustrialTile_XX.png` tiles. `industrial_tileset.py` loads files by the numeric suffix, with documented semantic aliases for metal panels, walkways, hazard trims, pipes, and supports.
- `backgrounds/`: the original `1.png` through `5.png` parallax layers and `Background.png` composite reference.
- `objects/`: non-colliding factory props (barrels, boxes, lockers, benches, fences, ladders, boards, fire extinguishers, and related objects).
- `animated_objects/`: original sprite strips. Explicit per-file frame dimensions are declared in `industrial_tileset.py`; they are sliced horizontally and cached once.

Decoration placement is deterministic for a level seed and level number. Props and animated machinery are visual only and do not create or modify collision geometry.

import { create } from 'zustand';
import type { DiscoverItem } from '../lib/types';

type OppStore = {
  items: DiscoverItem[];
  set: (items: DiscoverItem[]) => void;
  clear: () => void;
};

export const useOpportunities = create<OppStore>((set) => ({
  items: [],
  set: (items) => set({ items }),
  clear: () => set({ items: [] }),
}));

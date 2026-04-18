import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Profile } from '../lib/types';

export type OnboardingState = {
  vision: string;
  blockers: string;
  program: string;
  interest: string;
  semester: string;
  cvFileName: string | null;
  githubUrl: string;
  linkedinUrl: string;
  interests: string[];
  tumSsoId: string;
  tumPassword: string;
  tumSsoConnected: boolean;
  // commitment level
  commitment: 'whisper' | 'steady' | 'push';
  setField: <K extends keyof Omit<OnboardingState, 'setField' | 'reset'>>(
    key: K,
    value: OnboardingState[K],
  ) => void;
  hydrate: (profile: Partial<Profile>) => void;
  reset: () => void;
};

const defaults = {
  vision: '',
  blockers: '',
  program: '',
  interest: '',
  semester: '',
  cvFileName: null,
  githubUrl: '',
  linkedinUrl: '',
  interests: [] as string[],
  tumSsoId: '',
  tumPassword: '',
  tumSsoConnected: false,
  commitment: 'steady' as const,
};

export const useOnboarding = create<OnboardingState>()(
  persist(
    (set) => ({
      ...defaults,
      setField: (key, value) => set((s) => ({ ...s, [key]: value })),
      hydrate: (profile) =>
        set((state) => ({
          ...state,
          vision: profile.vision ?? state.vision,
          blockers: profile.blockers ?? state.blockers,
          program: profile.program ?? state.program,
          interest: profile.interest ?? state.interest,
          semester: profile.semester ?? state.semester,
          cvFileName: profile.cvFileName ?? state.cvFileName,
          githubUrl: profile.githubUrl ?? state.githubUrl,
          linkedinUrl: profile.linkedinUrl ?? state.linkedinUrl,
          interests: profile.interests ?? state.interests,
          tumSsoId: profile.tumSsoId ?? state.tumSsoId,
          tumSsoConnected: profile.tumSsoConnected ?? state.tumSsoConnected,
          commitment:
            profile.commitment === 'whisper' ||
            profile.commitment === 'steady' ||
            profile.commitment === 'push'
              ? profile.commitment
              : state.commitment,
        })),
      reset: () => set(defaults),
    }),
    { name: 'onboarding-v1' },
  ),
);

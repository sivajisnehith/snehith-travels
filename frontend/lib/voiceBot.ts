/**
 * Saarthi AI Voice Bot Configuration & Testing Notice.
 */

export interface VoiceBotLine {
  id: string;
  name: string;
  number: string;
  displayNumber: string;
  pin: string;
  isPrimary: boolean;
  badge: string;
  description: string;
}

export const VOICE_BOT_LINES: VoiceBotLine[] = [
  {
    id: 'primary',
    name: 'Main Voice Line',
    number: '09513885656',
    displayNumber: '09513885656',
    pin: '7396959239#',
    isPrimary: true,
    badge: 'Main (Recommended)',
    description: 'Primary active line for booking tickets over voice.',
  },
  {
    id: 'backup',
    name: 'Backup Voice Line',
    number: '09513886363',
    displayNumber: '09513886363',
    pin: '8712145983#',
    isPrimary: false,
    badge: 'Backup (Trial)',
    description: 'Secondary line (trial period expiring soon).',
  },
];

export const VOICE_BOT_CONFIG = {
  // Primary / Recommended Line (Main)
  phoneNumber: '09513885656',
  displayPhoneNumber: '09513885656',
  accessPassword: '7396959239#',

  // Secondary / Trial Line (Backup)
  backupPhoneNumber: '09513886363',
  backupAccessPassword: '8712145983#',

  // All Lines
  lines: VOICE_BOT_LINES,

  // Meta Cloud API restriction notice
  restrictedWhatsAppNumber: '8712145983',
  restrictedWhatsAppDisplay: '+91 8712145983',

  // Support notes
  supportedLanguages: ['English', 'Hindi', 'Telugu'],
};

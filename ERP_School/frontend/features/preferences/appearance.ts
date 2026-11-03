import type { Preferences } from '../../shared/types';
export const fontNames: Record<string, string> = { vazirmatn: 'وزیرمتن', estedad: 'استعداد', shabnam: 'شبنم', sahel: 'ساحل', samim: 'صمیم' };
export const themeNames: Record<string, string> = { sky: 'آبی آسمانی', emerald: 'سبز زمردی', violet: 'بنفش', amber: 'کهربایی', rose: 'رز' };
export const themeColors: Record<string, string> = { sky: '#0369a1', emerald: '#047857', violet: '#6d28d9', amber: '#92400e', rose: '#be123c' };
export const defaultAppearance: Preferences = { font: 'vazirmatn', size: 'normal', theme: 'sky', accent: '' };
export function applyAppearance(preferences: Preferences) {
    const root = document.documentElement;
    root.dataset.font = preferences.font;
    root.dataset.size = preferences.size;
    root.dataset.theme = preferences.theme;
    const color = /^#[0-9a-fA-F]{6}$/.test(preferences.accent) ? preferences.accent : themeColors[preferences.theme] || themeColors.sky;
    const channels = [1, 3, 5].map(offset => parseInt(color.slice(offset, offset + 2), 16) / 255).map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4);
    const luminance = channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722;
    root.style.setProperty('--accent', color);
    root.style.setProperty('--page', `color-mix(in srgb, ${color} 4%, #f6f8fb)`);
    root.style.setProperty('--accent-ink', luminance > .179 ? '#000000' : '#ffffff');
    localStorage.setItem('erp-school:appearance', JSON.stringify(preferences));
}
export function cachedAppearance(): Preferences {
    try {
        const value = JSON.parse(localStorage.getItem('erp-school:appearance') || 'null') as Preferences | null;
        return value && value.font in fontNames && value.theme in themeNames && ['small', 'normal', 'large'].includes(value.size) ? value : defaultAppearance;
    }
    catch {
        return defaultAppearance;
    }
}

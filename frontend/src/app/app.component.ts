import { Component, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

const THEME_STORAGE_KEY = 'camunda-ai-ops-theme';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  isDarkTheme = signal(false);

  constructor() {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    this.applyTheme(stored === 'dark');
  }

  toggleTheme(): void {
    this.applyTheme(!this.isDarkTheme());
  }

  private applyTheme(dark: boolean): void {
    this.isDarkTheme.set(dark);
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    localStorage.setItem(THEME_STORAGE_KEY, dark ? 'dark' : 'light');
  }
}

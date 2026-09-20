import { Routes } from '@angular/router';
import { PageComponent } from './page.component';

export const routes: Routes = [
  { path: '', component: PageComponent, data: { page: 'overview' } },
  { path: 'process-instances/:key', component: PageComponent, data: { page: 'instance-detail' } },
  { path: 'incidents/:key', component: PageComponent, data: { page: 'incident-detail' } },
  { path: 'investigation', component: PageComponent, data: { page: 'investigation' } },
  { path: 'knowledge-base', component: PageComponent, data: { page: 'knowledge' } },
  { path: '**', redirectTo: '' },
];

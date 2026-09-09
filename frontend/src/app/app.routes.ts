import { Routes } from '@angular/router';
import { PageComponent } from './page.component';

export const routes: Routes = [
  { path: '', component: PageComponent, data: { page: 'overview' } },
  { path: 'process-instances', component: PageComponent, data: { page: 'instances' } },
  { path: 'process-instances/:key', component: PageComponent, data: { page: 'instance-detail' } },
  { path: 'incidents', component: PageComponent, data: { page: 'incidents' } },
  { path: 'incidents/:key', component: PageComponent, data: { page: 'incident-detail' } },
  { path: 'process-definitions', component: PageComponent, data: { page: 'definitions' } },
  { path: 'process-definitions/:key', component: PageComponent, data: { page: 'definition-detail' } },
  { path: 'investigation', component: PageComponent, data: { page: 'investigation' } },
  { path: 'knowledge-base', component: PageComponent, data: { page: 'knowledge' } },
  { path: '**', redirectTo: '' },
];

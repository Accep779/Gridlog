const routes = [
  {
    path: '/login',
    component: () => import('pages/LoginPage.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/first-login',
    component: () => import('pages/FirstLoginPage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard' },
      {
        path: 'dashboard',
        component: () => import('pages/DashboardPage.vue'),
        meta: { roles: ['employee', 'supervisor', 'admin'] }
      },
      {
        path: 'reports',
        component: () => import('pages/ReportsList.vue'),
        meta: { roles: ['employee', 'supervisor', 'admin'] }
      },
      {
        path: 'reports/new',
        component: () => import('pages/ReportForm.vue'),
        meta: { roles: ['employee'], requiresEmployee: true }
      },
      {
        path: 'reports/:id',
        component: () => import('pages/ReportDetail.vue'),
        meta: { roles: ['employee', 'supervisor', 'admin'] }
      },
      {
        path: 'reports/:id/edit',
        component: () => import('pages/ReportForm.vue'),
        meta: { roles: ['employee'], requiresEmployee: true },
        props: route => ({ editMode: true, reportId: route.params.id })
      },
      {
        path: 'reports/:id/edit',
        component: () => import('pages/ReportForm.vue'),
        meta: { roles: ['employee'], requiresEmployee: true },
        props: route => ({ editMode: true, reportId: route.params.id })
      },
      {
        path: 'periods',
        component: () => import('pages/ReportingPeriodsPage.vue'),
        meta: { roles: ['admin'] }
      },
      {
        path: 'team-oversight',
        component: () => import('pages/TeamOversightPage.vue'),
        meta: { roles: ['supervisor'] }
      }
    ]
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
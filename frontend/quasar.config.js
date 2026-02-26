module.exports = function (/* ctx */) {
  const apiUrl = process.env.VITE_API_URL || 'http://localhost:8000'

  return {
    htmlVariables: { title: 'Gridlog' },
    css: ['app.scss'],

    devServer: {
      port: process.env.VITE_DEV_PORT || 9000,
      open: false,

      allowedHosts: [
        'localhost',
        '127.0.0.1'
      ],
      proxy: {
        '/api': {
          target: apiUrl,
          changeOrigin: true,
        }
      }
    },



    framework: {
      iconSet: 'material-icons',
      components: [
        'QBtn', 'QInput', 'QSelect', 'QTable', 'QCard', 'QCardSection',
        'QForm', 'QDialog', 'QBadge', 'QIcon', 'QSpinner', 'QBanner',
        'QList', 'QItem', 'QItemSection', 'QItemLabel', 'QPage', 'QLayout',
        'QHeader', 'QDrawer', 'QToolbar', 'QToolbarTitle', 'QSpace',
        'QAvatar', 'QChip', 'QTooltip', 'QSkeleton', 'QLinearProgress', 'QEditor'
      ],
      cssAddon: true,
      config: {
        brand: {
          primary: '#1976D2',
          secondary: '#8B5CF6',
          accent: '#EC4899',
          dark: '#0F172A',
          positive: '#10B981',
          negative: '#EF4444',
          info: '#06B6D4',
          warning: '#F59E0B'
        }
      },
      plugins: ['Notify', 'Dialog', 'Loading']
    },

    boot: [
      'axios',
      'router'
    ],

    animations: [],

    sourceFiles: {
      rootComponent: 'src/App.vue'
    }
  }
}
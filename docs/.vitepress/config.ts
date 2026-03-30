import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'ThirdRaven',
  description: 'Personal Entity & Relationship Manager',
  themeConfig: {
    nav: [
      { text: 'Guide', link: '/development' },
      { text: 'API', link: '/api-reference' },
    ],
    sidebar: [
      { text: 'Architecture', link: '/architecture' },
      { text: 'Data Models', link: '/data-models' },
      { text: 'Development', link: '/development' },
      { text: 'API Reference', link: '/api-reference' },
      { text: 'Vocabulary System', link: '/vocabulary-system' },
      {
        text: 'Specs',
        items: [
          { text: 'Person Entity', link: '/specs/person-entity-spec' },
          { text: 'Asset Entity', link: '/specs/asset-entity-spec' },
          { text: 'Migration Plan', link: '/specs/migration-plan' },
        ],
      },
    ],
  },
})

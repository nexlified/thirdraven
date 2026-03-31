import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'ThirdRaven',
  description: 'Personal Entity & Relationship Manager',
  // base must match the GitHub repository name when deploying to GitHub Pages
  // as a project site (https://<org>.github.io/thirdraven/).
  // Update this value if you deploy to a custom domain (set base: '/').
  base: '/thirdraven/',
  themeConfig: {
    nav: [
      { text: 'Guide', link: '/development' },
      { text: 'API', link: '/api-reference' },
      { text: 'dev', link: '/' },
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
      { text: 'Publishing Docs', link: '/publishing' },
    ],
  },
})

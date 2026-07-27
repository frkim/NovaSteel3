import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material'
import VerifiedOutlinedIcon from '@mui/icons-material/VerifiedOutlined'
import EnergySavingsLeafOutlinedIcon from '@mui/icons-material/EnergySavingsLeafOutlined'
import PublicOutlinedIcon from '@mui/icons-material/PublicOutlined'
import GroupsOutlinedIcon from '@mui/icons-material/GroupsOutlined'
import { useAnalytics } from '../../context/analytics'
import { WebsiteFooter, WebsitePage } from './CompanyWebsiteLayout'

const FLAT_PRODUCTS = [
  {
    title: 'Hot-rolled coils & sheets',
    body: 'Versatile, cost-effective steel for structural, mechanical, and general manufacturing applications.',
  },
  {
    title: 'Cold-rolled coils & sheets',
    body: 'Tighter tolerances and superior surface finish for automotive and appliance applications.',
  },
  {
    title: 'Heavy plate',
    body: 'Thick, high-strength plate for construction, shipbuilding, and heavy equipment.',
  },
  {
    title: 'Coated & galvanized steel',
    body: 'Zinc- and organic-coated steel offering enhanced corrosion protection.',
  },
]

const WHY_CARDS = [
  {
    icon: <VerifiedOutlinedIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
    title: 'Consistent quality',
    body: 'AI-stabilized processes deliver repeatable grades, batch after batch.',
  },
  {
    icon: <EnergySavingsLeafOutlinedIcon sx={{ fontSize: 40, color: 'success.main' }} />,
    title: 'Lower carbon footprint',
    body: 'Recycling and energy optimization reduce the embodied emissions of our steel.',
  },
  {
    icon: <PublicOutlinedIcon sx={{ fontSize: 40, color: 'info.main' }} />,
    title: 'European proximity',
    body: 'Production across four countries means reliable, responsive supply.',
  },
  {
    icon: <GroupsOutlinedIcon sx={{ fontSize: 40, color: 'warning.main' }} />,
    title: 'Expert support',
    body: 'Our metallurgical specialists help you select the right grade and product.',
  },
]

export function CompanyWebsiteProducts() {
  const { emit, site, t } = useAnalytics()

  function navigate(subView: string) {
    emit('nav.intent', { route: `/${site}/company-website/${subView}` })
  }

  return (
    <WebsitePage id="website-products" title={`AxelorMetal · ${t('website.nav.products')}`}>
      {/* ── Page header ── */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #1b2631 0%, #2e4057 60%, #1a5276 100%)',
          color: '#fff',
          py: { xs: 6, md: 8 },
          px: 2,
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="overline" sx={{ opacity: 0.7, letterSpacing: 3 }}>
            Products & Markets
          </Typography>
          <Typography variant="h1" sx={{ fontSize: { xs: '2rem', md: '3rem' }, fontWeight: 800, mt: 1 }}>
            Products
          </Typography>
          <Typography variant="h6" sx={{ mt: 2, opacity: 0.8, fontWeight: 400, maxWidth: 620 }}>
            AxelorMetal produces a broad portfolio of steel products, engineered to meet the exact
            mechanical, chemical, and dimensional requirements of our customers.
          </Typography>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ py: 8 }}>

        {/* ── Flat products ── */}
        <Typography variant="h3" gutterBottom>Flat products</Typography>
        <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
          Flat steel is produced by rolling slabs into sheets, plates, coils, and strips.
        </Typography>
        <Grid container spacing={3} sx={{ mb: 6 }}>
          {FLAT_PRODUCTS.map((p) => (
            <Grid key={p.title} size={{ xs: 12, sm: 6, md: 3 }}>
              <Card sx={{ height: '100%', border: 1, borderColor: 'divider' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>{p.title}</Typography>
                  <Typography variant="body2" color="text.secondary">{p.body}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* ── Long products ── */}
        <Typography variant="h3" gutterBottom>Long products</Typography>
        <Typography variant="body1" sx={{ mb: 2, color: 'text.secondary' }}>
          Long steel is produced by rolling blooms and billets into structural and linear shapes.
        </Typography>
        <List dense sx={{ mb: 5 }}>
          {[
            { primary: 'Beams and structural sections', secondary: 'for construction and infrastructure' },
            { primary: 'Rails', secondary: 'for railway networks' },
            { primary: 'Bars and rods', secondary: 'for machining, reinforcement, and manufacturing' },
            { primary: 'Wire rod', secondary: 'for drawing into wire, cable, and fasteners' },
          ].map((item) => (
            <ListItem key={item.primary} disableGutters>
              <ListItemText primary={<strong>{item.primary}</strong>} secondary={item.secondary} />
            </ListItem>
          ))}
        </List>

        {/* ── Grades & specialty steels ── */}
        <Typography variant="h3" gutterBottom>Grades and specialty steels</Typography>
        <Typography variant="body1" sx={{ mb: 2, color: 'text.secondary' }}>
          AxelorMetal produces a range of grades by carefully controlling carbon content and alloying
          elements:
        </Typography>
        <List dense sx={{ mb: 3 }}>
          {[
            { name: 'Carbon steels', desc: 'the workhorse grades balancing strength and cost.' },
            { name: 'High-strength low-alloy (HSLA) steels', desc: 'for lighter, stronger structures.' },
            { name: 'Stainless steels', desc: 'corrosion-resistant grades containing chromium.' },
            { name: 'Custom alloy steels', desc: 'with nickel, manganese, molybdenum, or other elements for specific properties.' },
          ].map((item) => (
            <ListItem key={item.name} disableGutters>
              <ListItemText primary={<><strong>{item.name}</strong> — {item.desc}</>} />
            </ListItem>
          ))}
        </List>

        <Alert severity="info" sx={{ mb: 5 }}>
          Want to understand the metallurgy? See{' '}
          <Button size="small" variant="text" onClick={() => navigate('steel-knowledge')} sx={{ textDecoration: 'underline', p: 0, minWidth: 0, verticalAlign: 'baseline' }}>
            Metal Families
          </Button>{' '}
          to learn how carbon and alloying elements change the properties of steel.
        </Alert>

        {/* ── Engineered for your application ── */}
        <Typography variant="h3" gutterBottom>Engineered for your application</Typography>
        <Typography variant="body1" sx={{ mb: 2, color: 'text.secondary' }}>Every product is backed by:</Typography>
        <List dense sx={{ mb: 6 }}>
          {[
            { name: 'Certified quality', desc: 'and full traceability' },
            { name: 'AI-stabilized processes', desc: 'for consistent, repeatable grades' },
            { name: 'Technical support', desc: 'from our metallurgical experts' },
          ].map((item) => (
            <ListItem key={item.name} disableGutters>
              <ListItemText primary={<><strong>{item.name}</strong> {item.desc}</>} />
            </ListItem>
          ))}
        </List>

        <Divider sx={{ my: 6 }} />

        {/* ── Markets ── */}
        <Typography variant="h2" gutterBottom>Markets We Serve</Typography>
        <Typography variant="body1" sx={{ mb: 5, color: 'text.secondary', maxWidth: 700 }}>
          AxelorMetal supplies certified steel to a diverse range of industries across Europe. Each
          market has its own demands — and our integrated, AI-optimized production is built to meet
          them.
        </Typography>

        <Stack spacing={4} sx={{ mb: 6 }}>
          {[
            {
              title: 'Automotive',
              intro: 'The automotive industry needs steel that is strong, light, and perfectly consistent. We supply cold-rolled and coated grades, including high-strength steels that help manufacturers reduce vehicle weight while improving safety.',
              items: [
                'High-strength and advanced high-strength steels',
                'Excellent surface quality for visible and structural parts',
                'Tight, repeatable tolerances backed by AI-stabilized processes',
              ],
            },
            {
              title: 'Construction & infrastructure',
              intro: 'From buildings to bridges and railways, construction relies on dependable structural steel.',
              items: [
                'Structural beams and sections',
                'Heavy plate',
                'Rails and reinforcing products',
              ],
            },
            {
              title: 'Energy',
              intro: 'The energy sector — from conventional power to renewables — requires durable, high-performance steel for demanding environments.',
              items: [
                'Plate and sections for equipment and structures',
                'Corrosion-resistant grades for harsh conditions',
              ],
            },
            {
              title: 'Industrial & mechanical manufacturing',
              intro: 'General manufacturing depends on a reliable supply of versatile steel.',
              items: [
                'Hot- and cold-rolled products',
                'Bars, rods, and wire rod',
                'Custom grades for specific mechanical requirements',
              ],
            },
          ].map((market) => (
            <Box key={market.title}>
              <Typography variant="h4" gutterBottom>{market.title}</Typography>
              <Typography variant="body1" sx={{ mb: 2 }} color="text.secondary">{market.intro}</Typography>
              <List dense>
                {market.items.map((item, i) => (
                  <ListItem key={i} disableGutters>
                    <ListItemText primary={item} />
                  </ListItem>
                ))}
              </List>
              <Divider sx={{ mt: 2 }} />
            </Box>
          ))}
        </Stack>

        {/* ── Why customers choose AxelorMetal ── */}
        <Typography variant="h3" gutterBottom>Why customers choose AxelorMetal</Typography>
        <Grid container spacing={3} sx={{ mt: 1, mb: 5 }}>
          {WHY_CARDS.map((card) => (
            <Grid key={card.title} size={{ xs: 12, sm: 6, md: 3 }}>
              <Card sx={{ height: '100%', border: 1, borderColor: 'divider' }}>
                <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  {card.icon}
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>{card.title}</Typography>
                  <Typography variant="body2" color="text.secondary">{card.body}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <Button variant="contained" size="large" onClick={() => navigate('products')} sx={{ fontWeight: 700 }}>
            Explore our products
          </Button>
          <Button variant="outlined" size="large" onClick={() => navigate('contact')} sx={{ fontWeight: 700 }}>
            {t('website.cta.getInTouch')}
          </Button>
        </Stack>
      </Container>

      <WebsiteFooter />
    </WebsitePage>
  )
}

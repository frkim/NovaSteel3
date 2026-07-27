import {
  Alert,
  Box,
  Card,
  CardActionArea,
  CardContent,
  Container,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Typography,
  Button,
} from '@mui/material'
import FactoryOutlinedIcon from '@mui/icons-material/FactoryOutlined'
import PrecisionManufacturingOutlinedIcon from '@mui/icons-material/PrecisionManufacturingOutlined'
import EnergySavingsLeafOutlinedIcon from '@mui/icons-material/EnergySavingsLeafOutlined'
import SchoolOutlinedIcon from '@mui/icons-material/SchoolOutlined'
import VerifiedOutlinedIcon from '@mui/icons-material/VerifiedOutlined'
import { useAnalytics } from '../../context/analytics'
import { WebsiteFooter, WebsitePage } from './CompanyWebsiteLayout'

const WHO_WE_ARE_CARDS = [
  {
    icon: <FactoryOutlinedIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
    title: 'Integrated production',
    body: 'Blast furnaces, basic oxygen furnaces, electric arc furnaces, and rolling mills operated as one connected, optimized system.',
    nav: 'company',
  },
  {
    icon: <PrecisionManufacturingOutlinedIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
    title: 'AI-driven optimization',
    body: 'Physics-informed machine learning predicts equipment wear, optimizes energy use, and captures operator expertise — powered by the NovaSteel platform.',
    nav: 'company',
  },
  {
    icon: <EnergySavingsLeafOutlinedIcon sx={{ fontSize: 40, color: 'success.main' }} />,
    title: 'Responsible steelmaking',
    body: 'Lower energy intensity, reduced CO₂ emissions, and a clear roadmap toward decarbonized steel.',
    nav: 'company',
  },
  {
    icon: <SchoolOutlinedIcon sx={{ fontSize: 40, color: 'secondary.main' }} />,
    title: 'Steel knowledge',
    body: 'Learn how iron, steel, and other metals are produced and shaped in modern industrial plants.',
    nav: 'steel-knowledge',
  },
] as const

const AT_A_GLANCE_ROWS = [
  { label: 'Headquarters', value: 'Luxembourg' },
  { label: 'Operating region', value: 'Luxembourg, Germany, Belgium, Spain' },
  { label: 'Industry', value: 'Heavy industry & metals' },
  { label: 'Production routes', value: 'Blast furnace / BOF and Electric arc furnace' },
  { label: 'Regulatory context', value: 'GDPR • EU AI Act • Sector-specific EU directives' },
]

const COMMITMENTS = [
  { label: 'Quality', detail: 'Consistent, certified grades for the most demanding customers.' },
  { label: 'Safety', detail: 'Protecting our people and our communities every day.' },
  { label: 'Sustainability', detail: 'Cutting energy use and emissions across every process.' },
  { label: 'Innovation', detail: 'Applying AI and data to a 5,000-year-old material.' },
]

export function CompanyWebsiteHome() {
  const { emit, site, t } = useAnalytics()

  function navigate(subView: string) {
    emit('nav.intent', { route: `/${site}/company-website/${subView}` })
  }

  return (
    <WebsitePage id="website-home" title={`AxelorMetal · ${t('website.nav.home')}`}>
      {/* ── Hero ── */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #0d1b2a 0%, #1b2a3b 45%, #263547 100%)',
          color: '#fff',
          py: { xs: 8, md: 12 },
          px: 2,
        }}
      >
        <Container maxWidth="lg">
          <Box
            component="img"
            src="/brand/axelormetal-wordmark.png"
            alt="AxelorMetal"
            height={52}
            onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
              e.currentTarget.style.display = 'none'
            }}
            sx={{ mb: 4, display: 'block' }}
          />
          <Typography
            variant="h1"
            sx={{ fontSize: { xs: '2.25rem', md: '3.75rem' }, fontWeight: 800, mb: 2, lineHeight: 1.1 }}
          >
            Engineering the future of steel
          </Typography>
          <Typography variant="h5" sx={{ mb: 5, opacity: 0.82, maxWidth: 680, fontWeight: 400 }}>
            AxelorMetal combines more than a century of metallurgical expertise with the{' '}
            <strong>NovaSteel AI optimization platform</strong> to deliver high-quality steel
            responsibly, efficiently, and sustainably.
          </Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('company')}
              aria-label={t('website.hero.cta.discover')}
              sx={{ fontWeight: 700, px: 4 }}
            >
              {t('website.hero.cta.discover')}
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('products')}
              aria-label={t('website.hero.cta.products')}
              sx={{
                color: '#fff',
                borderColor: 'rgba(255,255,255,0.6)',
                fontWeight: 700,
                px: 4,
                '&:hover': { borderColor: '#fff', backgroundColor: 'rgba(255,255,255,0.08)' },
              }}
            >
              {t('website.hero.cta.products')}
            </Button>
          </Stack>
        </Container>
      </Box>

      {/* ── Who we are ── */}
      <Container maxWidth="lg" sx={{ py: 10 }}>
        <Typography variant="h2" gutterBottom>
          Who we are
        </Typography>
        <Typography variant="body1" sx={{ mb: 6, maxWidth: 700, color: 'text.secondary', fontSize: '1.1rem' }}>
          We supply steel to demanding industries — automotive, construction, energy, and advanced
          manufacturing — across Luxembourg, Germany, Belgium, and Spain. From raw iron ore to
          finished rolled products, we control the full value chain while continuously reducing our
          environmental footprint.
        </Typography>
        <Grid container spacing={3}>
          {WHO_WE_ARE_CARDS.map((card) => (
            <Grid key={card.title} size={{ xs: 12, sm: 6, md: 3 }}>
              <Card
                sx={{ height: '100%', border: 1, borderColor: 'divider', boxShadow: 2 }}
              >
                <CardActionArea onClick={() => navigate(card.nav)} sx={{ height: '100%' }}>
                  <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, height: '100%' }}>
                    {card.icon}
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      {card.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {card.body}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* ── At a glance ── */}
      <Box sx={{ bgcolor: 'action.hover', py: 10, px: 2 }}>
        <Container maxWidth="lg">
          <Typography variant="h2" gutterBottom>
            AxelorMetal at a glance
          </Typography>
          <TableContainer sx={{ mt: 3, maxWidth: 700 }}>
            <Table size="small" aria-label="AxelorMetal at a glance">
              <TableBody>
                {AT_A_GLANCE_ROWS.map((row) => (
                  <TableRow key={row.label}>
                    <TableCell sx={{ fontWeight: 600, width: '40%', borderBottom: '1px solid', borderColor: 'divider' }}>
                      {row.label}
                    </TableCell>
                    <TableCell sx={{ borderBottom: '1px solid', borderColor: 'divider' }}>
                      {row.value}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Container>
      </Box>

      {/* ── Our commitments ── */}
      <Container maxWidth="lg" sx={{ py: 10 }}>
        <Typography variant="h2" gutterBottom>
          Our commitments
        </Typography>
        <List disablePadding>
          {COMMITMENTS.map((c) => (
            <ListItem key={c.label} disableGutters sx={{ py: 1 }}>
              <ListItemIcon sx={{ minWidth: 36 }}>
                <VerifiedOutlinedIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary={<strong>{c.label}</strong>}
                secondary={c.detail}
              />
            </ListItem>
          ))}
        </List>

        <Alert severity="info" sx={{ mt: 5, maxWidth: 700 }}>
          AxelorMetal operates across the European Union and aligns with the{' '}
          <strong>GDPR</strong>, the <strong>EU AI Act</strong>, and sector-specific EU directives,
          ensuring that our use of data and AI is transparent, fair, and accountable.
        </Alert>

        <Box sx={{ mt: 5 }}>
          <Button variant="contained" size="large" onClick={() => navigate('contact')} sx={{ fontWeight: 700, px: 4 }}>
            {t('website.cta.getInTouch')}
          </Button>
        </Box>
      </Container>

      <WebsiteFooter />
    </WebsitePage>
  )
}

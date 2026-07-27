import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material'
import HandshakeOutlinedIcon from '@mui/icons-material/HandshakeOutlined'
import GroupsOutlinedIcon from '@mui/icons-material/GroupsOutlined'
import EnergySavingsLeafOutlinedIcon from '@mui/icons-material/EnergySavingsLeafOutlined'
import WorkOutlineOutlinedIcon from '@mui/icons-material/WorkOutlineOutlined'
import LocationOnOutlinedIcon from '@mui/icons-material/LocationOnOutlined'
import { useAnalytics } from '../../context/analytics'
import { WebsiteFooter, WebsitePage } from './CompanyWebsiteLayout'

const CONTACT_CARDS = [
  {
    icon: <HandshakeOutlinedIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
    title: 'Sales & products',
    body: "Questions about our products, grades, or availability? Our commercial team is ready to help you find the right steel for your application.",
    nav: 'products',
    cta: 'Explore our products',
  },
  {
    icon: <GroupsOutlinedIcon sx={{ fontSize: 40, color: 'info.main' }} />,
    title: 'Partnerships',
    body: 'Interested in working with AxelorMetal on innovation, sustainability, or supply? Let\'s talk.',
    nav: 'company',
    cta: 'About AxelorMetal',
  },
  {
    icon: <EnergySavingsLeafOutlinedIcon sx={{ fontSize: 40, color: 'success.main' }} />,
    title: 'Sustainability',
    body: 'Learn about our climate ambition and our roadmap toward cleaner steel.',
    nav: 'company',
    cta: 'Sustainability',
  },
  {
    icon: <WorkOutlineOutlinedIcon sx={{ fontSize: 40, color: 'warning.main' }} />,
    title: 'Careers',
    body: 'Join a team building the future of steel with metallurgy, data, and AI.',
    nav: null,
    cta: null,
  },
]

const LOCATIONS = [
  { flag: '🇱🇺', country: 'Luxembourg', note: 'Headquarters' },
  { flag: '🇩🇪', country: 'Germany', note: null },
  { flag: '🇧🇪', country: 'Belgium', note: null },
  { flag: '🇪🇸', country: 'Spain', note: null },
]

export function CompanyWebsiteContact() {
  const { emit, site, t } = useAnalytics()

  function navigate(subView: string) {
    emit('nav.intent', { route: `/${site}/company-website/${subView}` })
  }

  return (
    <WebsitePage id="website-contact" title={`AxelorMetal · ${t('website.nav.contact')}`}>
      {/* ── Page header ── */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #0d1b2a 0%, #1b3a52 55%, #1a5276 100%)',
          color: '#fff',
          py: { xs: 6, md: 8 },
          px: 2,
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="overline" sx={{ opacity: 0.7, letterSpacing: 3 }}>
            Contact
          </Typography>
          <Typography variant="h1" sx={{ fontSize: { xs: '2rem', md: '3rem' }, fontWeight: 800, mt: 1 }}>
            Contact AxelorMetal
          </Typography>
          <Typography variant="h6" sx={{ mt: 2, opacity: 0.8, fontWeight: 400, maxWidth: 560 }}>
            We'd love to hear from you — whether you're a customer, a partner, a future colleague,
            or simply curious about steel.
          </Typography>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ py: 8 }}>
        {/* ── Head office ── */}
        <Typography variant="h3" gutterBottom>Head office</Typography>
        <Box sx={{ mb: 5, p: 3, border: 1, borderColor: 'divider', borderRadius: 2, maxWidth: 340 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>AxelorMetal S.A.</Typography>
          <Typography variant="body2" color="text.secondary">Luxembourg</Typography>
          <Typography variant="body2" color="text.secondary">European Union</Typography>
        </Box>

        {/* ── Get in touch ── */}
        <Typography variant="h3" gutterBottom>Get in touch</Typography>
        <Grid container spacing={3} sx={{ mb: 8 }}>
          {CONTACT_CARDS.map((card) => (
            <Grid key={card.title} size={{ xs: 12, sm: 6, md: 3 }}>
              <Card sx={{ height: '100%', border: 1, borderColor: 'divider' }}>
                <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, height: '100%' }}>
                  {card.icon}
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>{card.title}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1 }}>{card.body}</Typography>
                  {card.nav && card.cta && (
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => navigate(card.nav!)}
                      sx={{ alignSelf: 'flex-start', mt: 1 }}
                    >
                      {card.cta}
                    </Button>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* ── Where we operate ── */}
        <Typography variant="h3" gutterBottom>Where we operate</Typography>
        <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
          AxelorMetal operates blast furnaces and rolling mills across four European countries:
        </Typography>
        <List sx={{ maxWidth: 360, mb: 6 }}>
          {LOCATIONS.map((loc) => (
            <ListItem key={loc.country} disableGutters sx={{ py: 1 }}>
              <ListItemIcon sx={{ minWidth: 40 }}>
                <LocationOnOutlinedIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary={
                  <Typography variant="body1">
                    <span style={{ fontSize: '1.2em', marginRight: 8 }}>{loc.flag}</span>
                    <strong>{loc.country}</strong>
                    {loc.note && (
                      <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                        — {loc.note}
                      </Typography>
                    )}
                  </Typography>
                }
              />
            </ListItem>
          ))}
        </List>

        {/* ── GDPR privacy note ── */}
        <Alert severity="info" sx={{ mb: 5, maxWidth: 700 }}>
          <strong>Privacy:</strong> AxelorMetal processes personal data in accordance with the{' '}
          <strong>GDPR</strong>. Any information you share with us is handled responsibly and
          transparently. For more information, see our{' '}
          <Button
            size="small"
            variant="text"
            onClick={() => navigate('company')}
            sx={{ textDecoration: 'underline', p: 0, minWidth: 0, verticalAlign: 'baseline', fontSize: 'inherit' }}
          >
            Compliance page
          </Button>.
        </Alert>

        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <Button variant="contained" size="large" onClick={() => navigate('products')} sx={{ fontWeight: 700 }}>
            Explore our products
          </Button>
          <Button variant="outlined" size="large" onClick={() => navigate('company')} sx={{ fontWeight: 700 }}>
            {t('website.cta.learnMore')}
          </Button>
        </Stack>
      </Container>

      <WebsiteFooter />
    </WebsitePage>
  )
}

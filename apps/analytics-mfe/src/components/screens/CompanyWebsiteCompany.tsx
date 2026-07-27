import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Container,
  Divider,
  Link,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Card,
  CardContent,
  Grid,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import FactoryOutlinedIcon from '@mui/icons-material/FactoryOutlined'
import HardwareOutlinedIcon from '@mui/icons-material/HardwareOutlined'
import LocalShippingOutlinedIcon from '@mui/icons-material/LocalShippingOutlined'
import ScienceOutlinedIcon from '@mui/icons-material/ScienceOutlined'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined'
import { useAnalytics } from '../../context/analytics'
import { WebsiteFooter, WebsitePage } from './CompanyWebsiteLayout'

const ACTIVITY_CARDS = [
  {
    icon: <FactoryOutlinedIcon sx={{ fontSize: 36, color: 'primary.main' }} />,
    title: 'Raw materials & ironmaking',
    body: 'Sourcing iron ore, coke, scrap, and alloys, and producing molten iron in our blast furnaces.',
  },
  {
    icon: <ScienceOutlinedIcon sx={{ fontSize: 36, color: 'error.main' }} />,
    title: 'Steelmaking & refining',
    body: 'Converting iron into steel and adjusting composition to meet precise grade specifications.',
  },
  {
    icon: <HardwareOutlinedIcon sx={{ fontSize: 36, color: 'warning.main' }} />,
    title: 'Rolling & forming',
    body: 'Transforming cast steel into flat and long products through rolling mills.',
  },
  {
    icon: <LocalShippingOutlinedIcon sx={{ fontSize: 36, color: 'success.main' }} />,
    title: 'Distribution & service',
    body: 'Delivering certified products and technical support to customers across Europe.',
  },
]

export function CompanyWebsiteCompany() {
  const { emit, site, t } = useAnalytics()

  function navigate(subView: string) {
    emit('nav.intent', { route: `/${site}/company-website/${subView}` })
  }

  return (
    <WebsitePage id="website-company" title={`AxelorMetal · ${t('website.nav.company')}`}>
      {/* ── Page header ── */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%)',
          color: '#fff',
          py: { xs: 6, md: 8 },
          px: 2,
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="overline" sx={{ opacity: 0.7, letterSpacing: 3 }}>
            Company
          </Typography>
          <Typography variant="h1" sx={{ fontSize: { xs: '2rem', md: '3rem' }, fontWeight: 800, mt: 1 }}>
            About AxelorMetal
          </Typography>
          <Typography variant="h6" sx={{ mt: 2, opacity: 0.8, fontWeight: 400, maxWidth: 620 }}>
            A Luxembourg-based integrated steel producer pioneering the use of artificial intelligence
            to make steelmaking cleaner, safer, and more efficient.
          </Typography>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ py: 8 }}>
        {/* ── About ── */}
        <Accordion defaultExpanded disableGutters elevation={0} sx={{ border: 1, borderColor: 'divider', mb: 2, '&:before': { display: 'none' } }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ py: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>About AxelorMetal</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" sx={{ mb: 2 }}>
              AxelorMetal is a Luxembourg-based integrated steel producer. We transform raw materials
              into high-performance steel products for some of the most demanding industries in
              Europe, while pioneering the use of artificial intelligence to make steelmaking
              cleaner, safer, and more efficient.
            </Typography>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 3, mb: 1 }}>Our mission</Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              To produce the steel that builds modern society — responsibly, intelligently, and
              sustainably — by combining deep metallurgical expertise with advanced data and AI
              capabilities.
            </Typography>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 2, mb: 1 }}>Our vision</Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              A steel industry that is competitive <strong>and</strong> decarbonized, where digital
              intelligence amplifies human expertise rather than replacing it.
            </Typography>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 2, mb: 2 }}>Company profile</Typography>
            <TableContainer sx={{ maxWidth: 600 }}>
              <Table size="small" aria-label="Company profile">
                <TableBody>
                  {[
                    { label: 'Industry', value: 'Heavy industry & metals' },
                    { label: 'Headquarters', value: 'Luxembourg' },
                    { label: 'Operating region', value: 'Luxembourg, Germany, Belgium, Spain' },
                    { label: 'Production routes', value: 'Blast furnace / basic oxygen furnace and electric arc furnace' },
                    { label: 'Regulatory context', value: 'GDPR • EU AI Act • Sector-specific EU directives' },
                  ].map((row) => (
                    <TableRow key={row.label}>
                      <TableCell sx={{ fontWeight: 600, borderColor: 'divider' }}>{row.label}</TableCell>
                      <TableCell sx={{ borderColor: 'divider' }}>{row.value}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 3, mb: 1 }}>Our story</Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Founded on a long European tradition of iron and steelmaking, AxelorMetal has grown
              into an integrated producer operating blast furnaces and rolling mills across four
              countries. Today, we are writing the next chapter: the{' '}
              <strong>NovaSteel AI-driven production optimization platform</strong> that connects
              every furnace, mill, and sensor into a single, continuously learning system.
            </Typography>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 2, mb: 1 }}>The AxelorMetal difference</Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              AxelorMetal's NovaSteel platform is built around an <strong>AI infusion strategy</strong>{' '}
              that targets the hardest problems in steelmaking:
            </Typography>
            <List dense>
              {[
                'A physics-informed machine-learning model predicts furnace lining degradation from thermal signatures, providing up to 21 days of advance warning before a costly failure.',
                'An energy dispatch optimization agent schedules energy-intensive processes around electricity spot prices to lower cost and emissions.',
                'A generative-AI knowledge-capture system interviews experienced operators and structures their expertise into searchable procedure libraries, preserving know-how as skilled workers retire.',
              ].map((item, i) => (
                <ListItem key={i} disableGutters>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <CheckCircleOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={item} />
                </ListItem>
              ))}
            </List>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 3, mb: 1 }}>Measurable impact</Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3} sx={{ mt: 1 }}>
              {[
                { stat: '−14%', label: 'energy consumption per ton of steel' },
                { stat: '−22%', label: 'CO₂ emissions' },
                { stat: '+8%', label: 'high-grade steel yield' },
                { stat: '21 days', label: 'advance warning on furnace lining failures' },
              ].map((kpi) => (
                <Card key={kpi.stat} sx={{ flex: 1, textAlign: 'center', bgcolor: 'primary.main', color: 'primary.contrastText' }}>
                  <CardContent>
                    <Typography variant="h4" sx={{ fontWeight: 800 }}>{kpi.stat}</Typography>
                    <Typography variant="caption">{kpi.label}</Typography>
                  </CardContent>
                </Card>
              ))}
            </Stack>

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 4 }}>
              <Button variant="contained" onClick={() => navigate('products')}>Explore our activities</Button>
              <Button variant="outlined" onClick={() => navigate('company')}>Sustainability roadmap</Button>
            </Stack>
          </AccordionDetails>
        </Accordion>

        {/* ── Our Activities ── */}
        <Accordion disableGutters elevation={0} sx={{ border: 1, borderColor: 'divider', mb: 2, '&:before': { display: 'none' } }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ py: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>Our Activities</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" sx={{ mb: 2 }}>
              AxelorMetal operates across the full steel value chain — from raw materials to
              finished, customer-ready products. Our integrated model lets us control quality, cost,
              and environmental performance at every step.
            </Typography>

            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>Integrated steel production</Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              We run both of the major modern steelmaking routes, allowing us to balance output,
              flexibility, and sustainability:
            </Typography>
            <List dense>
              <ListItem disableGutters>
                <ListItemText
                  primary={<><strong>Blast furnace / basic oxygen furnace (BF/BOF) route</strong> — producing molten iron from iron ore, then converting it into high-quality steel.</>}
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary={<><strong>Electric arc furnace (EAF) route</strong> — melting recycled scrap steel to produce new steel with a lower carbon footprint.</>}
                />
              </ListItem>
            </List>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 2, mb: 1 }}>From liquid steel to finished products</Typography>
            <List dense>
              {[
                'Continuous casting of slabs, blooms, and billets',
                'Hot and cold rolling into sheets, plates, coils, strips, and structural sections',
                'Finishing operations such as coating, slitting, and inspection',
              ].map((item, i) => (
                <ListItem key={i} disableGutters>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <CheckCircleOutlineIcon color="action" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={item} />
                </ListItem>
              ))}
            </List>

            <Divider sx={{ my: 3 }} />

            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>Core activities at a glance</Typography>
            <Grid container spacing={2}>
              {ACTIVITY_CARDS.map((card) => (
                <Grid key={card.title} size={{ xs: 12, sm: 6 }}>
                  <Card sx={{ border: 1, borderColor: 'divider', height: '100%' }}>
                    <CardContent>
                      {card.icon}
                      <Typography variant="subtitle1" sx={{ fontWeight: 700, mt: 1 }}>{card.title}</Typography>
                      <Typography variant="body2" color="text.secondary">{card.body}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 3, mb: 1 }}>Research, data & AI</Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Beyond physical production, a growing share of AxelorMetal's activity is digital. Our
              data and AI teams build and operate the <strong>NovaSteel platform</strong> that:
            </Typography>
            <List dense>
              {[
                'Predicts equipment failures before they happen',
                'Optimizes energy use against real-time electricity prices',
                'Improves and stabilizes the quality of high-grade steel',
                'Captures and preserves the expertise of our most experienced operators',
              ].map((item, i) => (
                <ListItem key={i} disableGutters>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <CheckCircleOutlineIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={item} />
                </ListItem>
              ))}
            </List>

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 4 }}>
              <Button variant="contained" onClick={() => navigate('products')}>See our products</Button>
              <Button variant="outlined" onClick={() => navigate('products')}>Markets we serve</Button>
            </Stack>
          </AccordionDetails>
        </Accordion>

        {/* ── Sustainability ── */}
        <Accordion disableGutters elevation={0} sx={{ border: 1, borderColor: 'divider', mb: 2, '&:before': { display: 'none' } }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ py: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>Sustainability</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Steel is essential to modern life — and it can be made responsibly. AxelorMetal is
              committed to producing the materials society needs while sharply reducing the energy
              and emissions required to make them.
            </Typography>

            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>Our climate ambition</Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              The steel industry is energy-intensive and carbon-intensive by nature. We treat that
              as our biggest responsibility and our biggest opportunity. Our optimization program is
              built to deliver measurable environmental gains:
            </Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 3 }}>
              {[
                { stat: '−14%', label: 'energy consumption per ton of steel' },
                { stat: '−22%', label: 'CO₂ emissions' },
                { stat: '+8%', label: 'high-grade steel yield (less waste, more usable output)' },
              ].map((kpi) => (
                <Card key={kpi.stat} sx={{ flex: 1, bgcolor: 'success.main', color: 'success.contrastText', textAlign: 'center' }}>
                  <CardContent>
                    <Typography variant="h4" sx={{ fontWeight: 800 }}>{kpi.stat}</Typography>
                    <Typography variant="caption">{kpi.label}</Typography>
                  </CardContent>
                </Card>
              ))}
            </Stack>

            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>Levers for decarbonization</Typography>

            <Typography variant="subtitle2" sx={{ fontWeight: 700, mt: 2 }}>Energy efficiency</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Energy represents around <strong>35%</strong> of our total production cost. Our{' '}
              <strong>energy dispatch optimization agent</strong> schedules energy-intensive
              processes around electricity spot prices and grid conditions, cutting both cost and
              emissions without compromising output.
            </Typography>

            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Recycling and the electric arc furnace route</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Our <strong>electric arc furnace (EAF)</strong> operations melt recycled scrap steel
              into new steel. Because steel is <strong>100% recyclable</strong> without loss of
              quality, the EAF route is a cornerstone of a circular, lower-carbon steel economy.
            </Typography>

            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Predictive maintenance</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              A <strong>physics-informed machine-learning model</strong> predicts furnace lining
              degradation up to <strong>21 days</strong> in advance. Preventing catastrophic
              failures — each of which can cost around <strong>€8M</strong> — also avoids the
              energy, materials, and emissions wasted by unplanned shutdowns and restarts.
            </Typography>

            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Process optimization and quality</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              By improving high-grade steel yield by <strong>8%</strong>, we produce more usable
              material from the same raw materials and energy, reducing rework, scrap, and waste.
            </Typography>

            <Alert severity="info" sx={{ mt: 2 }}>
              AxelorMetal aligns with the <strong>EU Emissions Trading System (ETS)</strong>, the{' '}
              <strong>GDPR</strong>, the <strong>EU AI Act</strong>, and sector-specific EU
              directives for industrial emissions and safety.
            </Alert>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 3, mb: 1 }}>Preserving knowledge, protecting people</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Sustainability is also about people. Our <strong>generative-AI knowledge-capture
              system</strong> structures the expertise of retiring operators into searchable
              procedure libraries, keeping safe and efficient practices alive for the next generation
              of steelworkers.
            </Typography>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 2, mb: 1 }}>A pragmatic roadmap</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              We believe decarbonization must be <strong>measurable and achievable</strong>. Rather
              than distant promises, AxelorMetal focuses on concrete improvements — energy, yield,
              reliability, and recycling — that compound year after year toward a cleaner steel
              industry.
            </Typography>
          </AccordionDetails>
        </Accordion>

        {/* ── Compliance ── */}
        <Accordion disableGutters elevation={0} sx={{ border: 1, borderColor: 'divider', '&:before': { display: 'none' } }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ py: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>Compliance</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Alert severity="info" sx={{ mb: 3 }}>
              <strong>Disclaimer:</strong> This page is provided for general information only and
              does not constitute legal advice. Always refer to the official, up-to-date legal texts
              linked below for authoritative requirements.
            </Alert>

            <Typography variant="body1" sx={{ mb: 2 }}>
              Operating across the European Union, AxelorMetal embeds regulatory compliance into
              every process — from how we collect and protect data to how we design, deploy, and
              govern our AI systems.
            </Typography>

            {/* GDPR */}
            <Typography variant="h6" sx={{ fontWeight: 700, mt: 3, mb: 1 }}>
              GDPR — General Data Protection Regulation
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              The <strong>General Data Protection Regulation (EU) 2016/679 (GDPR)</strong> is the
              European Union's data-protection law. It governs how organizations collect, store, and
              process the <strong>personal data</strong> of individuals in the EU, and grants people
              rights over their own data — including access, rectification, erasure, and portability.
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              At AxelorMetal, GDPR shapes how we handle employee, operator, and partner data across
              the NovaSteel platform. We apply principles of <strong>data minimization</strong>,{' '}
              <strong>purpose limitation</strong>, and <strong>privacy by design</strong>, and we
              ensure that personal data used to train or operate our AI systems is processed
              lawfully, transparently, and securely.
            </Typography>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mt: 1 }}>Learn more:</Typography>
            <List dense>
              <ListItem disableGutters>
                <ListItemText primary={
                  <Link href="https://eur-lex.europa.eu/eli/reg/2016/679/oj" target="_blank" rel="noopener noreferrer">
                    Official GDPR text (EUR-Lex)
                  </Link>
                } />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText primary={
                  <Link href="https://commission.europa.eu/law/law-topic/data-protection_en" target="_blank" rel="noopener noreferrer">
                    European Commission — Data protection in the EU
                  </Link>
                } />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText primary={
                  <Link href="https://www.edpb.europa.eu/" target="_blank" rel="noopener noreferrer">
                    European Data Protection Board (EDPB)
                  </Link>
                } />
              </ListItem>
            </List>

            <Divider sx={{ my: 3 }} />

            {/* EU AI Act */}
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
              EU AI Act — Artificial Intelligence Act
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              The <strong>EU AI Act (Regulation (EU) 2024/1689)</strong> is the world's first
              comprehensive legal framework for artificial intelligence. It takes a{' '}
              <strong>risk-based approach</strong>, classifying AI systems by their potential
              impact — from minimal risk to high risk — and imposing stronger obligations
              (transparency, human oversight, data governance, and robustness) on higher-risk
              systems.
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              AxelorMetal's NovaSteel platform AI infusion strategy — predictive maintenance,
              energy-dispatch optimization, and generative knowledge capture — is designed for{' '}
              <strong>trustworthy, transparent, and human-centered AI</strong>. We keep operators
              in control, document how our models are built and validated, and monitor them in
              production to ensure they remain safe, fair, and accountable.
            </Typography>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mt: 1 }}>Learn more:</Typography>
            <List dense>
              <ListItem disableGutters>
                <ListItemText primary={
                  <Link href="https://eur-lex.europa.eu/eli/reg/2024/1689/oj" target="_blank" rel="noopener noreferrer">
                    Official EU AI Act text (EUR-Lex)
                  </Link>
                } />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText primary={
                  <Link href="https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai" target="_blank" rel="noopener noreferrer">
                    European Commission — AI Act overview
                  </Link>
                } />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText primary={
                  <Link href="https://artificialintelligenceact.eu/" target="_blank" rel="noopener noreferrer">
                    EU AI Act Explorer
                  </Link>
                } />
              </ListItem>
            </List>

            <Divider sx={{ my: 3 }} />

            {/* Sector-specific directives */}
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
              Sector-specific EU Directives
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Beyond data and AI, steelmaking is governed by a set of{' '}
              <strong>sector-specific EU directives and regulations</strong> covering industrial
              emissions, energy, worker safety, and carbon markets.
            </Typography>
            <TableContainer sx={{ mb: 2 }}>
              <Table size="small" aria-label="EU regulatory frameworks">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Framework</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>What it covers</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {[
                    { fw: 'Industrial Emissions Directive (IED)', covers: 'Permits and limits for pollutant emissions from large industrial installations.' },
                    { fw: 'EU Emissions Trading System (ETS)', covers: "The EU's carbon market, capping and pricing greenhouse-gas emissions from heavy industry." },
                    { fw: 'Carbon Border Adjustment Mechanism (CBAM)', covers: 'Carbon pricing on imports of carbon-intensive goods such as steel.' },
                    { fw: 'Occupational Safety & Health (OSH) framework', covers: "Protection of workers' health and safety in industrial environments." },
                  ].map((row) => (
                    <TableRow key={row.fw}>
                      <TableCell sx={{ fontWeight: 600 }}>{row.fw}</TableCell>
                      <TableCell>{row.covers}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <List dense>
              <ListItem disableGutters>
                <ListItemText primary={
                  <Link href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32010L0075" target="_blank" rel="noopener noreferrer">
                    Industrial Emissions Directive (EUR-Lex)
                  </Link>
                } />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText primary={
                  <Link href="https://climate.ec.europa.eu/eu-action/eu-emissions-trading-system-eu-ets_en" target="_blank" rel="noopener noreferrer">
                    EU Emissions Trading System (ETS)
                  </Link>
                } />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText primary={
                  <Link href="https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en" target="_blank" rel="noopener noreferrer">
                    Carbon Border Adjustment Mechanism (CBAM)
                  </Link>
                } />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText primary={
                  <Link href="https://osha.europa.eu/en" target="_blank" rel="noopener noreferrer">
                    EU-OSHA — Occupational safety and health
                  </Link>
                } />
              </ListItem>
            </List>

            <Alert severity="success" sx={{ mt: 3 }}>
              Compliance at AxelorMetal is not an afterthought — it is built into how we design our
              processes and our technology. By aligning with the <strong>GDPR</strong>, the{' '}
              <strong>EU AI Act</strong>, and sector-specific EU directives, we ensure that our use
              of data and AI is <strong>transparent, fair, and accountable</strong>.
            </Alert>

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 4 }}>
              <Button variant="contained" onClick={() => navigate('company')}>Sustainability roadmap</Button>
              <Button variant="outlined" onClick={() => navigate('company')}>About AxelorMetal</Button>
            </Stack>
          </AccordionDetails>
        </Accordion>
      </Container>

      <WebsiteFooter />
    </WebsitePage>
  )
}

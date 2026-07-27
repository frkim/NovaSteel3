import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Container,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import HardwareOutlinedIcon from '@mui/icons-material/HardwareOutlined'
import LocalFireDepartmentOutlinedIcon from '@mui/icons-material/LocalFireDepartmentOutlined'
import FlaskOutlinedIcon from '@mui/icons-material/BiotechOutlined'
import StarBorderOutlinedIcon from '@mui/icons-material/StarBorderOutlined'
import MenuBookOutlinedIcon from '@mui/icons-material/MenuBookOutlined'
import AtomIcon from '@mui/icons-material/Biotech'
import { DataTable, type DataTableColumn } from '../primitives/DataTable'
import { PanelCard } from './common'
import { useAnalytics } from '../../context/analytics'
import { WebsiteFooter, WebsitePage } from './CompanyWebsiteLayout'
import { ProcessDiagram } from './CompanyWebsiteDiagram'

// ── Glossary data ──────────────────────────────────────────────────────────────

type GlossaryRow = { id: string; term: string; meaning: string }

const GLOSSARY_ROWS: GlossaryRow[] = [
  { id: '1', term: 'Alloy', meaning: 'A material made by combining a metal with one or more other elements to improve its properties.' },
  { id: '2', term: 'Blast furnace', meaning: 'A high-temperature furnace used to produce molten iron from iron ore, coke, and limestone.' },
  { id: '3', term: 'Basic oxygen furnace', meaning: 'A converter that turns molten iron into steel by blowing oxygen into the metal to reduce carbon and impurities.' },
  { id: '4', term: 'Electric arc furnace', meaning: 'A furnace that melts scrap steel or other metallic inputs using electric arcs.' },
  { id: '5', term: 'Slag', meaning: 'A by-product that collects impurities during smelting or refining.' },
  { id: '6', term: 'Coke', meaning: 'A carbon-rich fuel made from coal, providing heat and the chemical reaction that removes oxygen from iron ore.' },
  { id: '7', term: 'Pig iron (hot metal)', meaning: 'The molten iron produced by a blast furnace, containing too much carbon to be used as steel directly.' },
  { id: '8', term: 'Non-ferrous metal', meaning: 'A metal that is not primarily based on iron, such as aluminum, copper, zinc, or titanium.' },
  { id: '9', term: 'Stainless steel', meaning: 'A corrosion-resistant steel containing chromium.' },
  { id: '10', term: 'Cast iron', meaning: 'An iron-based material with a higher carbon content than steel; hard but brittle.' },
]

const GLOSSARY_COLUMNS: DataTableColumn<GlossaryRow>[] = [
  { key: 'term', label: 'Term', type: 'text', searchable: true, sortable: true },
  { key: 'meaning', label: 'Definition', type: 'text', searchable: true, sortable: false },
]

// ── Overview cards ─────────────────────────────────────────────────────────────

const OVERVIEW_CARDS = [
  {
    icon: <AtomIcon sx={{ fontSize: 36, color: 'primary.main' }} />,
    title: 'Metal Families',
    body: 'Understand the difference between iron, steel, cast iron, stainless steel, and non-ferrous metals.',
    anchor: 'metal-families',
  },
  {
    icon: <LocalFireDepartmentOutlinedIcon sx={{ fontSize: 36, color: 'error.main' }} />,
    title: 'Making Iron & Steel',
    body: 'Discover the blast furnace, basic oxygen furnace, and electric arc furnace routes.',
    anchor: 'iron-steel',
  },
  {
    icon: <FlaskOutlinedIcon sx={{ fontSize: 36, color: 'secondary.main' }} />,
    title: 'Producing Other Metals',
    body: 'See how aluminum, copper, zinc, and other metals are extracted and refined.',
    anchor: 'other-metals',
  },
  {
    icon: <HardwareOutlinedIcon sx={{ fontSize: 36, color: 'warning.main' }} />,
    title: 'Shaping Metals',
    body: 'Learn how casting, rolling, forging, extrusion, drawing, and machining give metals their final form.',
    anchor: 'shaping',
  },
  {
    icon: <StarBorderOutlinedIcon sx={{ fontSize: 36, color: 'success.main' }} />,
    title: 'Key Takeaways',
    body: 'The essentials, summarized.',
    anchor: 'key-takeaways',
  },
  {
    icon: <MenuBookOutlinedIcon sx={{ fontSize: 36, color: 'info.main' }} />,
    title: 'Glossary',
    body: 'Definitions of the key terms used throughout this section.',
    anchor: 'glossary',
  },
]

export function CompanyWebsiteSteelKnowledge() {
  const { emit, site, t } = useAnalytics()

  function navigate(subView: string) {
    emit('nav.intent', { route: `/${site}/company-website/${subView}` })
  }

  function scrollTo(id: string) {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <WebsitePage id="website-steel-knowledge" title={`AxelorMetal · ${t('website.nav.steelKnowledge')}`}>
      {/* ── Page header ── */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #1a1a2e 0%, #162447 55%, #1f4068 100%)',
          color: '#fff',
          py: { xs: 6, md: 8 },
          px: 2,
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="overline" sx={{ opacity: 0.7, letterSpacing: 3 }}>
            Steel Knowledge
          </Typography>
          <Typography variant="h1" sx={{ fontSize: { xs: '2rem', md: '3rem' }, fontWeight: 800, mt: 1 }}>
            Steel, iron, and other metals
          </Typography>
          <Typography variant="h6" sx={{ mt: 2, opacity: 0.8, fontWeight: 400, maxWidth: 680 }}>
            A clear overview of what distinguishes iron, steel, cast iron, and other metals, and how
            they are produced and shaped in industrial plants.
          </Typography>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ py: 8 }}>
        {/* ── Intro ── */}
        <Typography variant="body1" sx={{ mb: 2, fontSize: '1.1rem', maxWidth: 760 }}>
          Steel is one of the most important materials in the world — but it is often confused with
          iron and other metals. This knowledge hub explains, in plain language, what these materials
          are, how they are made, and how they are turned into the products we use every day.
        </Typography>

        <Alert severity="info" sx={{ mb: 5, maxWidth: 760 }}>
          If you are new to metallurgy, begin with <strong>Metal Families</strong> below and follow
          the sections in order.
        </Alert>

        {/* ── Overview cards ── */}
        <Typography variant="h2" gutterBottom>What you'll learn</Typography>
        <Grid container spacing={3} sx={{ mb: 8 }}>
          {OVERVIEW_CARDS.map((card) => (
            <Grid key={card.title} size={{ xs: 12, sm: 6, md: 4 }}>
              <Card sx={{ height: '100%', border: 1, borderColor: 'divider', boxShadow: 1 }}>
                <CardActionArea onClick={() => scrollTo(card.anchor)} sx={{ height: '100%' }}>
                  <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                    {card.icon}
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>{card.title}</Typography>
                    <Typography variant="body2" color="text.secondary">{card.body}</Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* ── Metal Families ── */}
        <Accordion id="metal-families" defaultExpanded disableGutters elevation={0} sx={{ border: 1, borderColor: 'divider', mb: 2, '&:before': { display: 'none' }, scrollMarginTop: 24 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ py: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>Metal Families</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" sx={{ mb: 2 }}>
              <strong>Iron</strong> is a chemical element and one of the most important raw materials
              in industry. In its pure form, it is relatively soft and not usually used alone for
              heavy-duty applications.
            </Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              <strong>Steel</strong> is not a pure metal: it is an <strong>alloy</strong> made mainly
              of iron with a small amount of carbon. This carbon content gives steel much better
              strength, hardness, and durability than pure iron.
            </Typography>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 2, mb: 1 }}>Iron-based materials</Typography>

            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Cast iron</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Cast iron is also based on iron, but it contains <strong>more carbon than steel</strong>.
              This makes it very hard and good for casting, but also <strong>more brittle</strong>.
            </Typography>

            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Stainless steel</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Stainless steel is a special type of steel that contains <strong>chromium</strong>,
              which forms a protective surface layer and helps prevent rust.
            </Typography>

            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Alloy steels</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Other alloying elements — such as <strong>nickel, manganese, molybdenum, or cobalt</strong>{' '}
              — can be added to create steels with specific properties.
            </Typography>

            <Alert severity="info" sx={{ my: 2 }}>
              <strong>Carbon makes the difference:</strong> Moving from pure iron, to steel, to cast
              iron, the <strong>carbon content increases</strong>. More carbon generally means more
              hardness — but also more brittleness.
            </Alert>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 3, mb: 2 }}>Comparison of iron-based materials</Typography>
            <TableContainer>
              <Table size="small" aria-label="Iron-based materials comparison">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Material</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Main composition</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Key characteristic</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {[
                    { mat: 'Iron', comp: 'Iron (pure element)', key: 'Relatively soft; rarely used alone for heavy duty' },
                    { mat: 'Steel', comp: 'Iron + small amount of carbon', key: 'Strong, hard, durable' },
                    { mat: 'Cast iron', comp: 'Iron + higher carbon than steel', key: 'Very hard, good for casting, but brittle' },
                    { mat: 'Stainless steel', comp: 'Steel + chromium', key: 'Corrosion-resistant' },
                    { mat: 'Alloy steels', comp: 'Steel + nickel, manganese, molybdenum, cobalt…', key: 'Tailored, specific properties' },
                  ].map((row) => (
                    <TableRow key={row.mat}>
                      <TableCell sx={{ fontWeight: 600 }}>{row.mat}</TableCell>
                      <TableCell>{row.comp}</TableCell>
                      <TableCell>{row.key}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 3, mb: 1 }}>Non-ferrous metals</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Metals that are <strong>not primarily based on iron</strong> are called{' '}
              <strong>non-ferrous metals</strong>. They are important because they offer properties
              that iron-based materials cannot always provide.
            </Typography>
            <List dense>
              {[
                { name: 'Aluminum', desc: 'light and corrosion-resistant' },
                { name: 'Copper', desc: 'conducts electricity very well' },
                { name: 'Zinc', desc: 'often used to protect steel from corrosion' },
                { name: 'Titanium', desc: 'combines high strength with low weight' },
              ].map((item) => (
                <ListItem key={item.name} disableGutters>
                  <ListItemText primary={<><strong>{item.name}</strong> — {item.desc}</>} />
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>

        {/* ── Making Iron & Steel ── */}
        <Accordion id="iron-steel" disableGutters elevation={0} sx={{ border: 1, borderColor: 'divider', mb: 2, '&:before': { display: 'none' }, scrollMarginTop: 24 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ py: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>Making Iron & Steel</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" sx={{ mb: 2 }}>
              There are two main modern routes for making steel: the{' '}
              <strong>blast furnace / basic oxygen furnace</strong> route and the{' '}
              <strong>electric arc furnace</strong> route. AxelorMetal operates both.
            </Typography>

            <ProcessDiagram
              stem="steel-route-blast-furnace"
              title="The integrated route, end to end"
              alt="Illustrated overview of the steps of steel creation: raw material extraction, ironmaking in a blast furnace, steelmaking in a basic oxygen furnace with secondary metallurgy, continuous casting, rolling and shaping, and finished products."
              caption="Iron ore, coke and limestone enter on the left; coils, plates, rebar and structural sections leave on the right. The six numbered stages are read left to right."
            />

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 2, mb: 1 }}>The blast furnace route</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              One traditional way to make steel starts with a <strong>blast furnace</strong>. In this
              route, <strong>iron ore, coke, and limestone</strong> are charged into a very tall
              furnace. Coke — a carbon-rich fuel made from coal — provides both the{' '}
              <strong>heat</strong> and the <strong>chemical reaction</strong> needed to remove oxygen
              from the iron ore. The furnace operates at extremely high temperatures, producing:
            </Typography>
            <List dense>
              <ListItem disableGutters>
                <ListItemText primary={<><strong>Molten iron</strong>, also called hot metal or pig iron</>} />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText primary="A separate waste layer called slag" />
              </ListItem>
            </List>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 2, mb: 1 }}>The basic oxygen furnace</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Molten iron from the blast furnace contains <strong>too much carbon</strong> to be used
              as steel. It is therefore transferred into a{' '}
              <strong>basic oxygen furnace</strong> (converter). Pure <strong>oxygen</strong> is blown
              onto the molten metal, burning off excess carbon and reducing unwanted impurities.
            </Typography>

            <Alert severity="info" sx={{ my: 2 }}>
              <strong>From iron to steel:</strong> The blast furnace makes <strong>iron</strong>. The
              basic oxygen furnace turns that iron into <strong>steel</strong> by removing most of
              the carbon.
            </Alert>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 2, mb: 1 }}>The electric arc furnace route</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Another major route is the <strong>electric arc furnace (EAF)</strong>. Instead of
              starting mainly from iron ore, this process usually melts{' '}
              <strong>recycled scrap steel</strong> using powerful electric arcs generated by graphite
              electrodes. The molten steel is then refined and adjusted to the required composition.
              This route supports <strong>recycling</strong> and is{' '}
              <strong>flexible</strong> for producing different grades of steel.
            </Typography>

            <ProcessDiagram
              stem="steel-route-electric-arc-furnace"
              title="The same journey, starting from scrap"
              alt="Illustrated overview of steel creation via the electric arc furnace: scrap and raw material preparation, melting in an electric arc furnace powered by electricity, ladle refining, continuous casting, rolling and shaping, and finished products."
              caption="The casting, rolling and finishing stages are identical to the integrated route. What changes is the front end: recycled scrap and electricity replace iron ore and coke."
            />

            <ProcessDiagram
              stem="eaf-process-detail"
              title="Inside the electric arc furnace, step by step"
              alt="Detailed ten-step diagram of steel creation with an electric arc furnace: raw material preparation, charging the furnace, melting with electric arcs, oxygen injection and refining, slag formation, tapping the furnace, secondary metallurgy in a ladle furnace, continuous casting, hot rolling, and finished steel products."
              caption="A closer look at the ten operations behind the EAF route — the same equipment the Furnace Health and Energy Optimization screens of this portal monitor in real time."
            />

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 3, mb: 2 }}>Comparing the two routes</Typography>
            <TableContainer>
              <Table size="small" aria-label="Steelmaking routes comparison">
                <TableHead>
                  <TableRow>
                    <TableCell />
                    <TableCell sx={{ fontWeight: 700 }}>Blast furnace / BOF</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Electric arc furnace</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {[
                    { label: 'Main input', bf: 'Iron ore, coke, limestone', eaf: 'Recycled scrap steel' },
                    { label: 'Energy source', bf: 'Coke (chemical + heat)', eaf: 'Electricity' },
                    { label: 'Key strength', bf: 'Large-scale primary production', eaf: 'Recycling and flexibility' },
                  ].map((row) => (
                    <TableRow key={row.label}>
                      <TableCell sx={{ fontWeight: 600 }}>{row.label}</TableCell>
                      <TableCell>{row.bf}</TableCell>
                      <TableCell>{row.eaf}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>

        {/* ── Producing Other Metals ── */}
        <Accordion id="other-metals" disableGutters elevation={0} sx={{ border: 1, borderColor: 'divider', mb: 2, '&:before': { display: 'none' }, scrollMarginTop: 24 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ py: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>Producing Other Metals</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Other metals are produced through different industrial processes depending on their ore
              and chemical properties. In every case, the goal is the same: separate the useful metal
              from the ore, remove impurities, and obtain a material with predictable mechanical,
              chemical, or electrical properties.
            </Typography>

            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>Aluminum</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Aluminum is extracted from <strong>bauxite</strong>:
            </Typography>
            <List dense>
              <ListItem disableGutters><ListItemText primary="1. The bauxite is refined into alumina." /></ListItem>
              <ListItem disableGutters><ListItemText primary="2. The alumina is then transformed into aluminum through an electrolysis process." /></ListItem>
            </List>
            <Typography variant="body2" sx={{ mb: 2 }}>
              This requires a large amount of <strong>electricity</strong>, which is why aluminum
              production is strongly linked to energy availability.
            </Typography>

            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>Copper</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>Copper is generally produced by:</Typography>
            <List dense>
              <ListItem disableGutters><ListItemText primary="1. Concentrating copper ore" /></ListItem>
              <ListItem disableGutters><ListItemText primary="2. Smelting it at high temperature" /></ListItem>
              <ListItem disableGutters><ListItemText primary="3. Refining it to improve purity" /></ListItem>
            </List>

            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>Other industrial metals</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              <strong>Zinc, titanium, nickel,</strong> and other industrial metals each require
              specific extraction and refining methods suited to their ore and chemistry.
            </Typography>

            <Alert severity="info" sx={{ my: 2 }}>
              <strong>A common goal:</strong> Whatever the metal, production aims to{' '}
              <strong>separate the useful metal from the ore, remove impurities, and deliver
              predictable properties</strong> — mechanical, chemical, or electrical.
            </Alert>

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 2, mb: 2 }}>Summary</Typography>
            <TableContainer>
              <Table size="small" aria-label="Other metals summary">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Metal</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Typical source</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Key step</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {[
                    { metal: 'Aluminum', source: 'Bauxite', step: 'Electrolysis of alumina (energy-intensive)' },
                    { metal: 'Copper', source: 'Copper ore', step: 'Concentration, smelting, refining' },
                    { metal: 'Zinc, titanium, nickel…', source: 'Various ores', step: 'Specific extraction and refining methods' },
                  ].map((row) => (
                    <TableRow key={row.metal}>
                      <TableCell sx={{ fontWeight: 600 }}>{row.metal}</TableCell>
                      <TableCell>{row.source}</TableCell>
                      <TableCell>{row.step}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>

        {/* ── Shaping Metals ── */}
        <Accordion id="shaping" disableGutters elevation={0} sx={{ border: 1, borderColor: 'divider', mb: 2, '&:before': { display: 'none' }, scrollMarginTop: 24 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ py: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>Shaping Metals</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Once a metal has been produced and refined, it must be{' '}
              <strong>shaped into usable products</strong>. The method depends on the desired object,
              the metal's properties, the required strength, and the production volume. Some techniques
              shape <strong>molten</strong> metal, while others deform <strong>solid</strong> metal
              under heat or pressure.
            </Typography>

            {[
              { tech: 'Casting', desc: 'Molten metal is poured into a mold and allowed to solidify. This is useful for complex shapes such as engine blocks, valves, or machine parts.' },
              { tech: 'Rolling', desc: 'Hot or cold metal is passed between large rollers to reduce thickness or create sheets, plates, rails, beams, or strips.' },
              { tech: 'Forging', desc: 'Metal is compressed, hammered, or pressed into shape. This improves strength and is used for tools, crankshafts, gears, and high-stress components.' },
              { tech: 'Extrusion', desc: 'Metal is forced through a shaped die to create long products with a constant cross-section, such as tubes, rods, and aluminum profiles.' },
              { tech: 'Drawing', desc: 'Metal is pulled through a die to reduce its diameter, commonly used for wires, cables, and tubes.' },
              { tech: 'Machining', desc: 'Material is removed by cutting, drilling, milling, or turning to achieve precise dimensions and surface finishes.' },
            ].map((item) => (
              <Box key={item.tech} sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{item.tech}</Typography>
                <Typography variant="body2" color="text.secondary">{item.desc}</Typography>
              </Box>
            ))}

            <Typography variant="h6" sx={{ fontWeight: 700, mt: 3, mb: 2 }}>At a glance</Typography>
            <TableContainer>
              <Table size="small" aria-label="Shaping techniques">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Technique</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>What happens</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Typical products</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {[
                    { tech: 'Casting', what: 'Molten metal poured into a mold', products: 'Engine blocks, valves, machine parts' },
                    { tech: 'Rolling', what: 'Metal passed between rollers', products: 'Sheets, plates, rails, beams, strips' },
                    { tech: 'Forging', what: 'Metal hammered or pressed', products: 'Tools, crankshafts, gears' },
                    { tech: 'Extrusion', what: 'Metal forced through a die', products: 'Tubes, rods, aluminum profiles' },
                    { tech: 'Drawing', what: 'Metal pulled through a die', products: 'Wires, cables, tubes' },
                    { tech: 'Machining', what: 'Material removed by cutting', products: 'Precise, finished components' },
                  ].map((row) => (
                    <TableRow key={row.tech}>
                      <TableCell sx={{ fontWeight: 600 }}>{row.tech}</TableCell>
                      <TableCell>{row.what}</TableCell>
                      <TableCell>{row.products}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>

        {/* ── Key Takeaways ── */}
        <Accordion id="key-takeaways" disableGutters elevation={0} sx={{ border: 1, borderColor: 'divider', mb: 4, '&:before': { display: 'none' }, scrollMarginTop: 24 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ py: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>Key Takeaways</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" sx={{ mb: 2 }}>
              The essentials of iron, steel, and metal production — summarized.
            </Typography>
            <List>
              {[
                <><strong>Iron</strong> is a pure element, while <strong>steel</strong> is an alloy made mainly of iron and carbon.</>,
                <><strong>Cast iron</strong> contains more carbon than steel, making it hard but more brittle.</>,
                <><strong>Stainless steel</strong> resists corrosion because it contains chromium.</>,
                <>The two main modern steelmaking routes are the <strong>blast furnace / basic oxygen furnace route</strong> and the <strong>electric arc furnace route</strong>.</>,
                <>After production, metals are shaped through <strong>casting, rolling, forging, extrusion, drawing, and machining</strong>.</>,
              ].map((item, i) => (
                <ListItem key={i} disableGutters>
                  <ListItemText primary={item} />
                </ListItem>
              ))}
            </List>

            <Alert severity="success" sx={{ mt: 2 }}>
              <strong>Go deeper:</strong> Revisit Metal Families for the differences between
              materials, see Making Iron &amp; Steel for the production routes, and check the
              Glossary below for definitions of key terms.
            </Alert>

            <Box sx={{ mt: 3 }}>
              <Button variant="outlined" onClick={() => scrollTo('glossary')}>
                Read the glossary
              </Button>
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* ── Glossary (DataTable) ── */}
        <Box id="glossary" sx={{ scrollMarginTop: 24 }}>
          <PanelCard title="Glossary">
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Definitions of the key terms used throughout the Steel Knowledge section. Use the
              search box to find a term quickly.
            </Typography>
            <DataTable<GlossaryRow>
              rows={GLOSSARY_ROWS}
              columns={GLOSSARY_COLUMNS}
              getRowId={(row) => row.id}
              caption="Steel knowledge glossary — searchable and sortable"
              defaultSort={[{ key: 'term', direction: 'asc' }]}
              exportFileName="axelormetal-steel-glossary"
              initialPageSize={10}
              pageSizeOptions={[10, 25]}
            />
          </PanelCard>
        </Box>

        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 5 }}>
          <Button variant="outlined" onClick={() => navigate('steel-knowledge')}>
            Steel Knowledge overview
          </Button>
          <Button variant="text" onClick={() => navigate('products')}>
            Explore our products
          </Button>
        </Stack>
      </Container>

      <WebsiteFooter />
    </WebsitePage>
  )
}

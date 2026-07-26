import { useMemo, useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Divider,
  InputAdornment,
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import ScheduleIcon from '@mui/icons-material/Schedule'
import { useAnalytics } from '../../context/analytics'
import { PanelCard, SectionStack, TwoColumn, revealPanel } from './common'
import {
  dashboardCollectionTags,
  dashboardCollections,
  type DashboardCollection,
} from './dashboardCollectionCatalog'

/**
 * Curated dashboard collections (UX §9.8). Each collection is an ordered route
 * list that answers one question, so a persona can walk an investigation
 * instead of guessing which tab holds the next piece of evidence.
 */
export function DashboardCollections() {
  const { emit, site, t } = useAnalytics()
  const [query, setQuery] = useState('')
  const [tag, setTag] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string>(dashboardCollections[0].id)

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase()
    return dashboardCollections.filter((collection) => {
      if (tag && !collection.tags.includes(tag)) {
        return false
      }
      if (!needle) {
        return true
      }
      const haystack = [
        collection.title,
        collection.question,
        collection.persona,
        collection.narrative,
        ...collection.tags,
        ...collection.cards.map((card) => `${card.title} ${card.description}`),
      ]
        .join(' ')
        .toLowerCase()
      return haystack.includes(needle)
    })
  }, [query, tag])

  const selected: DashboardCollection =
    visible.find((collection) => collection.id === selectedId) ?? visible[0] ?? dashboardCollections[0]

  const open = (section: string, subView: string) => {
    emit('nav.intent', { route: `/${site}/${section}/${subView}` })
  }

  const openFirst = (collection: DashboardCollection) => {
    const first = collection.cards[0]
    open(first.section, first.subView)
  }

  return (
    <SectionStack>
      <PanelCard
        title={t('dashboards.title')}
        action={
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
            <TextField
              size="small"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={t('dashboards.search')}
              sx={{ minWidth: 220 }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                },
                htmlInput: { 'aria-label': t('dashboards.search') },
              }}
            />
          </Stack>
        }
      >
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {t('dashboards.intro')}
        </Typography>
        <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
          <Chip
            size="small"
            label={t('dashboards.allTags')}
            color={tag === null ? 'primary' : 'default'}
            variant={tag === null ? 'filled' : 'outlined'}
            onClick={() => setTag(null)}
          />
          {dashboardCollectionTags.map((entry) => (
            <Chip
              key={entry}
              size="small"
              label={entry}
              color={tag === entry ? 'primary' : 'default'}
              variant={tag === entry ? 'filled' : 'outlined'}
              onClick={() => setTag(tag === entry ? null : entry)}
            />
          ))}
        </Stack>
      </PanelCard>

      <TwoColumn
        sideWidth={380}
        main={
          <Box
            component="section"
            aria-label={t('dashboards.title')}
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr', md: 'repeat(auto-fit, minmax(300px, 1fr))' },
            }}
          >
            {visible.map((collection) => (
              <Card
                key={collection.id}
                component="article"
                aria-label={collection.title}
                sx={{
                  height: '100%',
                  outline: collection.id === selected.id ? 2 : 0,
                  outlineColor: 'primary.main',
                }}
              >
                <CardActionArea
                  aria-label={`${collection.title}: ${collection.question}`}
                  sx={{ alignItems: 'stretch', height: '100%', textAlign: 'left' }}
                  onClick={() => {
                    setSelectedId(collection.id)
                    revealPanel('dashboard-collection-detail')
                  }}
                >
                  <CardContent>
                    <Stack spacing={0.75} sx={{ height: '100%' }}>
                      <Typography variant="h3">{collection.title}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {collection.question}
                      </Typography>
                      <Box sx={{ flex: 1 }} />
                      <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
                        <Chip size="small" variant="outlined" label={collection.persona} />
                        <Chip
                          size="small"
                          variant="outlined"
                          icon={<ScheduleIcon />}
                          label={t('dashboards.minutes', { minutes: collection.estimatedMinutes })}
                        />
                        <Chip
                          size="small"
                          variant="outlined"
                          label={t('dashboards.panels', { count: collection.cards.length })}
                        />
                      </Stack>
                    </Stack>
                  </CardContent>
                </CardActionArea>
              </Card>
            ))}
            {visible.length === 0 && (
              <Typography variant="body2" color="text.secondary">
                {t('dashboards.empty')}
              </Typography>
            )}
          </Box>
        }
        side={
          <PanelCard
            id="dashboard-collection-detail"
            title={selected.title}
            action={
              <Tooltip title={t('dashboards.openAllHint')}>
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<PlayArrowIcon />}
                  onClick={() => openFirst(selected)}
                >
                  {t('dashboards.start')}
                </Button>
              </Tooltip>
            }
          >
            <Stack spacing={1}>
              <Typography variant="body2" color="text.secondary">
                {selected.narrative}
              </Typography>
              <Divider />
              <List dense disablePadding>
                {selected.cards.map((card, index) => (
                  <ListItem
                    key={card.id}
                    disableGutters
                    secondaryAction={
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => open(card.section, card.subView)}
                        aria-label={t('dashboards.openPanel', { panel: card.title })}
                      >
                        {t('dashboards.open')}
                      </Button>
                    }
                  >
                    <ListItemText
                      primary={`${index + 1}. ${card.title}`}
                      secondary={
                        <>
                          {card.description}
                          <Box component="span" sx={{ display: 'block', fontStyle: 'italic', mt: 0.25 }}>
                            {card.takeaway}
                          </Box>
                        </>
                      }
                      slotProps={{
                        primary: { variant: 'body2', sx: { fontWeight: 700 } },
                        secondary: { variant: 'caption', component: 'span' },
                      }}
                      sx={{ pr: 8 }}
                    />
                  </ListItem>
                ))}
              </List>
            </Stack>
          </PanelCard>
        }
      />
    </SectionStack>
  )
}

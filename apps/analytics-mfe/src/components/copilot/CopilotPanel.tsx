import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert,
  Autocomplete,
  Box,
  Chip,
  CircularProgress,
  Divider,
  FormControlLabel,
  IconButton,
  Link,
  MenuItem,
  Paper,
  Stack,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material'
import AddCommentIcon from '@mui/icons-material/AddComment'
import CloseIcon from '@mui/icons-material/Close'
import GppGoodIcon from '@mui/icons-material/GppGood'
import LayersIcon from '@mui/icons-material/Layers'
import MicIcon from '@mui/icons-material/Mic'
import MicOffIcon from '@mui/icons-material/MicOff'
import SendIcon from '@mui/icons-material/Send'
import TravelExploreIcon from '@mui/icons-material/TravelExplore'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'
import type {
  CopilotClient,
  CopilotConversationSummary,
  CopilotMessage,
  CopilotSource,
  ReasoningTier,
} from '../../api/copilotClient'
import { SUPPORTED_LANGUAGES, createTranslator, languageOf } from '../../i18n/messages'
import { LocaleFlag } from '../primitives/LocaleFlag'
import { ConversationList } from './ConversationList'
import { GlossaryBox } from './GlossaryBox'
import { useDictation } from './useDictation'

const LANGUAGE_LABELS: Record<string, string> = {
  en: 'EN/GB',
  fr: 'FR',
  de: 'DE',
  nl: 'NL',
  es: 'ES',
}

const CONTEXT_KEY = 'copilot-context-enabled'

interface PersonaQuestion {
  persona: string
  question: string
}

const PERSONA_QUESTIONS: PersonaQuestion[] = [
  { persona: 'Marc Weber', question: 'Which line is furthest behind target today?' },
  { persona: 'Marc Weber', question: 'Why did the night shift have lower yield than usual?' },
  { persona: 'Marc Weber', question: 'What should I prioritise in this morning\u2019s triage?' },
  { persona: 'Marc Weber', question: 'What is the current overall equipment effectiveness (OEE)?' },
  { persona: 'Elena Duarte', question: 'What is the current thermal profile of BF-01 hearth?' },
  { persona: 'Elena Duarte', question: 'Why is the temperature rising at sensor T12-North?' },
  { persona: 'Elena Duarte', question: 'What tap parameters should I adjust for the next cast?' },
  { persona: 'Elena Duarte', question: 'How does coke rate affect hearth wear?' },
  { persona: 'Tomás Rossi', question: 'Which assets have the highest failure probability this week?' },
  { persona: 'Tomás Rossi', question: 'Why is the predicted RUL dropping faster than the historical trend?' },
  { persona: 'Tomás Rossi', question: 'What maintenance should I schedule before the next planned stop?' },
  { persona: 'Tomás Rossi', question: 'What is the difference between P50 and P90 remaining useful life?' },
  { persona: 'Sofia Lindqvist', question: 'When is the next low-carbon electricity window today?' },
  { persona: 'Sofia Lindqvist', question: 'Why did energy intensity spike during the last shift?' },
  { persona: 'Sofia Lindqvist', question: 'What load-shift opportunities can save the most this week?' },
  { persona: 'Sofia Lindqvist', question: 'What is the Scope 2 emissions impact of shifting EAF heats to off-peak?' },
  { persona: 'Jens Bakker', question: 'Which coils failed the surface quality check today?' },
  { persona: 'Jens Bakker', question: 'Why is the defect rate trending up on Line 3?' },
  { persona: 'Jens Bakker', question: 'What process parameters correlate with centreline segregation?' },
  { persona: 'Jens Bakker', question: 'What is statistical process control telling us about thickness variation?' },
  { persona: 'Amina Haddad', question: 'Are we on track to meet this quarter\u2019s ETS compliance target?' },
  { persona: 'Amina Haddad', question: 'What would a 10% production increase mean for our CBAM exposure?' },
  { persona: 'Amina Haddad', question: 'What is our current carbon intensity per tonne of steel?' },
  { persona: 'Amina Haddad', question: 'How does our emissions performance compare to the benchmark?' },
  { persona: 'Pieter Claes', question: 'Which glossary terms are most frequently looked up?' },
  { persona: 'Pieter Claes', question: 'How does the Copilot decide which sources to cite?' },
  { persona: 'Pieter Claes', question: 'What is the knowledge grounding architecture of this platform?' },
  { persona: 'Pieter Claes', question: 'What are the guardrails against prompt injection?' },
  { persona: 'Isabelle Moreau', question: 'Give me a one-paragraph executive summary of plant performance today.' },
  { persona: 'Isabelle Moreau', question: 'What are the top three risks across all sites this week?' },
  { persona: 'Isabelle Moreau', question: 'How does this month\u2019s energy cost compare to budget?' },
  { persona: 'Isabelle Moreau', question: 'What is the business case for the hydrogen-DRI pilot?' },
  { persona: 'Rui Almeida', question: 'Which OT data feeds are currently delayed or missing?' },
  { persona: 'Rui Almeida', question: 'What is the polling latency for the furnace sensor network?' },
  { persona: 'Rui Almeida', question: 'How do I configure a new PLC tag for ingestion?' },
  { persona: 'Rui Almeida', question: 'What communication protocol does the thermal sensor array use?' },
  { persona: 'Nils Andersen', question: 'What is the current API response time for the BFF layer?' },
  { persona: 'Nils Andersen', question: 'Are there any unhealthy pods in the analytics cluster?' },
  { persona: 'Nils Andersen', question: 'What infrastructure changes were deployed in the last 24 hours?' },
  { persona: 'Nils Andersen', question: 'How do I scale up the ingestion pipeline for a new site?' },
]

export interface CopilotPanelProps {
  client: CopilotClient
  /** Screen slug the chat treats as context, e.g. `furnace-health`. */
  section: string
  subView?: string
  site?: string
  /** Human-readable screen title, shown in the context chip. */
  screenTitle: string
  persona: string
  locale: string
  onClose?: () => void
}

interface Bubble extends CopilotMessage {
  /** Present on assistant bubbles so the tier that answered stays visible. */
  tier?: string
}

/**
 * Renders the constrained markdown the answer engine emits: paragraphs
 * separated by blank lines, `**bold**` spans and `_italic_` disclaimers. A full
 * markdown renderer is deliberately avoided so model output can never inject
 * links or HTML into the dashboard.
 */
function RichText({ content }: { content: string }) {
  const paragraphs = content.split(/\n{2,}/)
  return (
    <>
      {paragraphs.map((paragraph, index) => (
        <Typography
          key={index}
          variant="body2"
          sx={{ mb: index === paragraphs.length - 1 ? 0 : 1, whiteSpace: 'pre-wrap' }}
        >
          {paragraph.split(/(\*\*[^*]+\*\*|_[^_]+_)/g).map((token, tokenIndex) => {
            if (token.startsWith('**') && token.endsWith('**')) {
              return (
                <Box component="strong" key={tokenIndex} sx={{ fontWeight: 700 }}>
                  {token.slice(2, -2)}
                </Box>
              )
            }
            if (token.length > 2 && token.startsWith('_') && token.endsWith('_')) {
              return (
                <Box component="em" key={tokenIndex} sx={{ opacity: 0.8 }}>
                  {token.slice(1, -1)}
                </Box>
              )
            }
            return <span key={tokenIndex}>{token}</span>
          })}
        </Typography>
      ))}
    </>
  )
}

function SourceList({ sources, t }: { sources: CopilotSource[]; t: (key: string) => string }) {
  if (sources.length === 0) {
    return null
  }
  const label = (kind: CopilotSource['kind']) => {
    switch (kind) {
      case 'online':
        return t('copilot.sources.online')
      case 'glossary':
        return t('copilot.sources.glossary')
      case 'screen':
        return t('copilot.sources.screen')
      case 'knowledge':
        return t('copilot.sources.internal')
      default:
        return t('copilot.sources.internal')
    }
  }
  return (
    <Box sx={{ mt: 1 }} data-testid="copilot-sources">
      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
        {t('copilot.sources')}
      </Typography>
      <Stack spacing={0.25} sx={{ mt: 0.25 }}>
        {sources.map((source, index) => (
          <Stack
            key={`${source.kind}-${source.sourceId}`}
            direction="row"
            spacing={0.5}
            sx={{ alignItems: 'center' }}
            data-testid="copilot-source"
          >
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, minWidth: 16 }}>
              [{index + 1}]
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {label(source.kind)} ·{' '}
              {source.url ? (
                <Link href={source.url} target="_blank" rel="noopener noreferrer">
                  {source.title}
                </Link>
              ) : (
                source.title
              )}
              {source.retrievedAt && (
                <> · {source.retrievedAt}</>
              )}
            </Typography>
            {source.offlineCorpus && (
              <Chip
                size="small"
                label={t('copilot.sources.offlineCorpus')}
                sx={{ height: 16, fontSize: '0.6rem' }}
              />
            )}
          </Stack>
        ))}
      </Stack>
    </Box>
  )
}

export function CopilotPanel({
  client,
  section,
  subView,
  site,
  screenTitle,
  persona,
  locale,
  onClose,
}: CopilotPanelProps) {
  const [language, setLanguage] = useState(() => languageOf(locale))
  const t = useMemo(() => createTranslator(language), [language])

  const [messages, setMessages] = useState<Bubble[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [conversations, setConversations] = useState<CopilotConversationSummary[]>([])
  const [draft, setDraft] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [onlineSearch, setOnlineSearch] = useState(false)
  const [temporary, setTemporary] = useState(false)
  const [reasoning, setReasoning] = useState<ReasoningTier>('auto')
  const [contextEnabled, setContextEnabled] = useState(() => {
    try { return localStorage.getItem(CONTEXT_KEY) === 'true' } catch { return false }
  })
  const transcriptRef = useRef<HTMLDivElement | null>(null)

  const dictation = useDictation(language, (text) =>
    setDraft((current) => (current ? `${current} ${text}` : text)),
  )

  const toggleContext = useCallback(() => {
    setContextEnabled((prev) => {
      const next = !prev
      try { localStorage.setItem(CONTEXT_KEY, String(next)) } catch { /* noop */ }
      return next
    })
  }, [])

  // Grouped suggestions: current persona first
  const groupedSuggestions = useMemo(() => {
    const forPersona = PERSONA_QUESTIONS.filter((q) => q.persona === persona)
    const rest = PERSONA_QUESTIONS.filter((q) => q.persona !== persona)
    return [...forPersona, ...rest]
  }, [persona])

  const refreshConversations = useCallback(() => {
    client
      .conversations()
      .then(setConversations)
      .catch(() => setConversations([]))
  }, [client])

  useEffect(refreshConversations, [refreshConversations])

  useEffect(() => {
    const transcript = transcriptRef.current
    // `scrollTo` is absent in jsdom and in a few older engines.
    if (transcript && typeof transcript.scrollTo === 'function') {
      transcript.scrollTo({ top: transcript.scrollHeight })
    }
  }, [messages, pending])

  const ask = useCallback(
    async (question: string) => {
      const trimmed = question.trim()
      if (!trimmed || pending) {
        return
      }
      setError(null)
      setPending(true)
      setDraft('')
      const optimistic: Bubble = {
        messageId: `local-${Date.now()}`,
        role: 'user',
        content: trimmed,
        createdAt: new Date().toISOString(),
        sources: [],
      }
      setMessages((current) => [...current, optimistic])
      try {
        const answer = await client.chat(
          {
            question: trimmed,
            conversationId: temporary ? undefined : conversationId ?? undefined,
            locale: language,
            reasoning,
            onlineSearch,
            temporary,
            context: contextEnabled ? { section, subView, site } : undefined,
          },
          t('copilot.offline'),
        )
        setMessages((current) => [
          ...current.slice(0, -1),
          answer.question,
          { ...answer.answer, tier: answer.resolvedReasoning },
        ])
        if (answer.persisted) {
          setConversationId(answer.conversationId)
          refreshConversations()
        }
      } catch {
        setMessages((current) => current.slice(0, -1))
        setDraft(trimmed)
        setError(t('copilot.error'))
      } finally {
        setPending(false)
      }
    },
    [
      client,
      contextEnabled,
      conversationId,
      language,
      onlineSearch,
      pending,
      reasoning,
      refreshConversations,
      section,
      site,
      subView,
      t,
      temporary,
    ],
  )

  const startNewChat = () => {
    setConversationId(null)
    setMessages([])
    setError(null)
  }

  const openConversation = async (id: string) => {
    try {
      const conversation = await client.conversation(id)
      setConversationId(conversation.conversationId)
      setMessages(conversation.messages)
      setError(null)
    } catch {
      setError(t('copilot.error'))
    }
  }

  const deleteConversation = async (id: string) => {
    const previousConversations = conversations
    const previousConversationId = conversationId
    const previousMessages = messages
    const wasActive = id === conversationId

    setConversations((current) => current.filter((c) => c.conversationId !== id))
    if (wasActive) {
      startNewChat()
    }

    try {
      await client.deleteConversation(id)
    } catch {
      setConversations(previousConversations)
      if (wasActive) {
        setConversationId(previousConversationId)
        setMessages(previousMessages)
      }
      setError(t('copilot.error'))
    }
  }

  const deleteAllConversations = async () => {
    const previousConversations = conversations
    setConversations([])
    startNewChat()
    try {
      await client.deleteAllConversations()
    } catch {
      setConversations(previousConversations)
      setError(t('copilot.error'))
    }
  }

  return (
    <Stack
      data-testid="copilot-panel"
      sx={{ height: '100%', minHeight: 0, bgcolor: 'background.paper' }}
    >
      <Stack
        direction="row"
        spacing={1}
        sx={{ alignItems: 'center', px: 1.5, py: 1, borderBottom: 1, borderColor: 'divider' }}
      >
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
            {t('copilot.title')}
          </Typography>
          <Typography variant="caption" color="text.secondary" noWrap>
            {t('copilot.subtitle')}
          </Typography>
        </Box>
        <Tooltip title={t('copilot.language')}>
          <TextField
            select
            size="small"
            value={language}
            onChange={(event) => setLanguage(event.target.value)}
            data-testid="copilot-language"
            slotProps={{ htmlInput: { 'aria-label': t('copilot.language') } }}
            sx={{ width: 104, '& .MuiInputBase-input': { py: 0.5, fontSize: '0.78rem' } }}
          >
            {SUPPORTED_LANGUAGES.map((code) => (
              <MenuItem key={code} value={code}>
                <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.75 }}>
                  <LocaleFlag code={code} />
                  <Box component="span">{LANGUAGE_LABELS[code]}</Box>
                </Box>
              </MenuItem>
            ))}
          </TextField>
        </Tooltip>
        <Tooltip title={t('copilot.temporary.hint')}>
          <IconButton
            size="small"
            aria-label={t('copilot.temporary')}
            aria-pressed={temporary}
            color={temporary ? 'primary' : 'default'}
            onClick={() => setTemporary((value) => !value)}
          >
            <VisibilityOffIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={t('copilot.context.toggle.hint')}>
          <IconButton
            size="small"
            aria-label={t('copilot.context.toggle')}
            aria-pressed={contextEnabled}
            data-testid="copilot-context-toggle"
            color={contextEnabled ? 'primary' : 'default'}
            onClick={toggleContext}
          >
            <LayersIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={t('copilot.conversations.new')}>
          <IconButton size="small" aria-label={t('copilot.conversations.new')} onClick={startNewChat}>
            <AddCommentIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        {onClose && (
          <Tooltip title={t('copilot.close')}>
            <IconButton size="small" aria-label={t('copilot.close')} onClick={onClose}>
              <CloseIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Stack>

      <Stack
        direction="row"
        spacing={1}
        sx={{ alignItems: 'center', px: 1.5, py: 0.75, flexWrap: 'wrap', rowGap: 0.5 }}
      >
        <GppGoodIcon fontSize="small" sx={{ color: 'success.main' }} />
        <Typography
          variant="caption"
          data-testid="copilot-shield"
          sx={{ color: 'success.main', fontWeight: 600 }}
        >
          {t('copilot.shield')}
        </Typography>
      </Stack>

      <Stack direction="row" spacing={1} sx={{ px: 1.5, pb: 1, flexWrap: 'wrap', rowGap: 0.5 }}>
        {contextEnabled && (
          <Chip
            size="small"
            variant="outlined"
            data-testid="copilot-context-chip"
            label={t('copilot.context.screen', { screen: screenTitle })}
          />
        )}
        {!contextEnabled && (
          <Chip
            size="small"
            variant="outlined"
            label={t('copilot.context.off')}
          />
        )}
        {temporary && <Chip size="small" color="primary" variant="outlined" label={t('copilot.temporary')} />}
      </Stack>

      <Box
        ref={transcriptRef}
        data-testid="copilot-transcript"
        role="log"
        aria-live="polite"
        aria-relevant="additions text"
        aria-busy={pending}
        aria-label={t('copilot.transcript')}
        sx={{ flexGrow: 1, minHeight: 0, overflowY: 'auto', px: 1.5, py: 1 }}
      >
        {messages.length === 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2">{t('copilot.empty.title')}</Typography>
            <Typography variant="caption" color="text.secondary">
              {t('copilot.empty.body')}
            </Typography>
          </Box>
        )}
        <Stack spacing={1.25}>
          {messages.map((message) => (
            <Paper
              key={message.messageId}
              elevation={0}
              variant="outlined"
              data-testid={`copilot-message-${message.role}`}
              sx={{
                p: 1.25,
                borderRadius: 2,
                alignSelf: message.role === 'user' ? 'flex-end' : 'stretch',
                maxWidth: message.role === 'user' ? '85%' : '100%',
                bgcolor: message.role === 'user' ? 'action.hover' : 'background.paper',
              }}
            >
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                {message.role === 'user' ? t('copilot.you') : t('copilot.assistant')}
                {message.tier ? ` · ${t('copilot.answeredWith', { tier: t(`copilot.reasoning.${message.tier}`) })}` : ''}
              </Typography>
              <RichText content={message.content} />
              <SourceList sources={message.sources} t={t} />
            </Paper>
          ))}
        </Stack>
        {pending && (
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mt: 1.5 }} role="status">
            <CircularProgress size={14} />
            <Typography variant="caption" color="text.secondary">
              {t('copilot.thinking')}
            </Typography>
          </Stack>
        )}
        {error && (
          <Alert severity="error" sx={{ mt: 1.5 }} role="alert">
            {error}
          </Alert>
        )}
      </Box>

      {messages.length === 0 && (
        <Box sx={{ px: 1.5, pb: 1 }} data-testid="copilot-suggestions">
          <Autocomplete
            size="small"
            options={groupedSuggestions}
            groupBy={(option) => option.persona}
            getOptionLabel={(option) => `${option.persona} – ${option.question}`}
            onChange={(_, value) => {
              if (value) setDraft(value.question)
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                placeholder={t('copilot.suggestions.grouped')}
                data-testid="copilot-suggestion"
              />
            )}
            renderOption={(props, option) => (
              <li {...props} key={`${option.persona}-${option.question}`}>
                <Typography variant="body2" noWrap>{option.question}</Typography>
              </li>
            )}
            blurOnSelect
            clearOnBlur={false}
            sx={{ mt: 0.5 }}
          />
        </Box>
      )}

      <Divider />

      <Box sx={{ px: 1.5, py: 1 }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            size="small"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                void ask(draft)
              }
            }}
            placeholder={t('copilot.placeholder')}
            data-testid="copilot-input"
            slotProps={{ htmlInput: { 'aria-label': t('copilot.placeholder') } }}
          />
          <Tooltip
            title={
              dictation.supported
                ? dictation.listening
                  ? t('copilot.mic.stop')
                  : t('copilot.mic.start')
                : t('copilot.mic.unsupported')
            }
          >
            <span>
              <IconButton
                size="small"
                disabled={!dictation.supported}
                aria-label={dictation.listening ? t('copilot.mic.stop') : t('copilot.mic.start')}
                color={dictation.listening ? 'error' : 'default'}
                onClick={() => (dictation.listening ? dictation.stop() : dictation.start())}
              >
                {dictation.supported ? <MicIcon fontSize="small" /> : <MicOffIcon fontSize="small" />}
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title={t('copilot.send')}>
            <span>
              <IconButton
                size="small"
                color="primary"
                aria-label={t('copilot.send')}
                data-testid="copilot-send"
                disabled={pending || !draft.trim()}
                onClick={() => void ask(draft)}
              >
                <SendIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </Stack>

        {dictation.listening && (
          <Typography variant="caption" color="error" role="status">
            {t('copilot.mic.listening')}
          </Typography>
        )}

        <Stack
          direction="row"
          spacing={1}
          sx={{ alignItems: 'center', mt: 1, flexWrap: 'wrap', rowGap: 0.5 }}
        >
          <Tooltip title={t('copilot.onlineSearch.hint')}>
            <FormControlLabel
              sx={{ mr: 0 }}
              control={
                <Switch
                  size="small"
                  checked={onlineSearch}
                  onChange={(event) => setOnlineSearch(event.target.checked)}
                  slotProps={{ input: { 'aria-label': t('copilot.onlineSearch') } }}
                />
              }
              label={
                <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
                  <TravelExploreIcon fontSize="small" />
                  <Typography variant="caption">{t('copilot.onlineSearch')}</Typography>
                </Stack>
              }
            />
          </Tooltip>
          <Box sx={{ flexGrow: 1 }} />
          <Tooltip title={t('copilot.reasoning.hint')}>
            <ToggleButtonGroup
              exclusive
              size="small"
              value={reasoning}
              aria-label={t('copilot.reasoning')}
              onChange={(_, value: ReasoningTier | null) => value && setReasoning(value)}
            >
              <ToggleButton value="auto">{t('copilot.reasoning.auto')}</ToggleButton>
              <ToggleButton value="default">{t('copilot.reasoning.default')}</ToggleButton>
              <ToggleButton value="high">{t('copilot.reasoning.high')}</ToggleButton>
            </ToggleButtonGroup>
          </Tooltip>
        </Stack>

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {t('copilot.synthetic')}
        </Typography>
      </Box>

      <Divider />

      <Box sx={{ px: 1.5, py: 1.25, maxHeight: '38%', overflowY: 'auto' }}>
        <GlossaryBox client={client} language={language} section={section} t={t} />
        <Box sx={{ mt: 1.5 }}>
          <ConversationList
            conversations={conversations}
            activeId={conversationId}
            onOpen={(id) => void openConversation(id)}
            onDelete={(id) => void deleteConversation(id)}
            onDeleteAll={() => void deleteAllConversations()}
            t={t}
          />
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {t('copilot.dock.hint')}
        </Typography>
      </Box>
    </Stack>
  )
}

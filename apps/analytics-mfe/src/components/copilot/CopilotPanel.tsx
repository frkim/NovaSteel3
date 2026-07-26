import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert,
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
import { ConversationList } from './ConversationList'
import { GlossaryBox } from './GlossaryBox'
import { useDictation } from './useDictation'

const LANGUAGE_LABELS: Record<string, string> = {
  en: 'EN/US',
  fr: 'FR',
  de: 'DE',
  nl: 'NL',
  es: 'ES',
}

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
        {sources.map((source) => (
          <Typography key={`${source.kind}-${source.sourceId}`} variant="caption" color="text.secondary">
            {label(source.kind)} ·{' '}
            {source.url ? (
              <Link href={source.url} target="_blank" rel="noopener noreferrer">
                {source.title}
              </Link>
            ) : (
              source.title
            )}
          </Typography>
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
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [draft, setDraft] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [onlineSearch, setOnlineSearch] = useState(false)
  const [temporary, setTemporary] = useState(false)
  const [reasoning, setReasoning] = useState<ReasoningTier>('auto')
  const transcriptRef = useRef<HTMLDivElement | null>(null)

  const dictation = useDictation(language, (text) =>
    setDraft((current) => (current ? `${current} ${text}` : text)),
  )

  const refreshConversations = useCallback(() => {
    client
      .conversations()
      .then(setConversations)
      .catch(() => setConversations([]))
  }, [client])

  useEffect(refreshConversations, [refreshConversations])

  useEffect(() => {
    let cancelled = false
    client
      .suggestions(section, language)
      .then((result) => {
        if (!cancelled) {
          setSuggestions(result.questions)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSuggestions([])
        }
      })
    return () => {
      cancelled = true
    }
  }, [client, section, language])

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
            context: { section, subView, site },
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
    await client.deleteConversation(id).catch(() => undefined)
    if (id === conversationId) {
      startNewChat()
    }
    refreshConversations()
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
        <TextField
          select
          size="small"
          value={language}
          onChange={(event) => setLanguage(event.target.value)}
          label={t('copilot.language')}
          sx={{ width: 108 }}
        >
          {SUPPORTED_LANGUAGES.map((code) => (
            <MenuItem key={code} value={code}>
              {LANGUAGE_LABELS[code]}
            </MenuItem>
          ))}
        </TextField>
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
        <Typography variant="caption" sx={{ color: 'success.main', fontWeight: 600 }}>
          {t('copilot.shield')}
        </Typography>
      </Stack>

      <Stack direction="row" spacing={1} sx={{ px: 1.5, pb: 1, flexWrap: 'wrap', rowGap: 0.5 }}>
        <Chip
          size="small"
          variant="outlined"
          data-testid="copilot-context-chip"
          label={t('copilot.context.screen', { screen: screenTitle })}
        />
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

      {suggestions.length > 0 && messages.length === 0 && (
        <Box sx={{ px: 1.5, pb: 1 }} data-testid="copilot-suggestions">
          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
            {t('copilot.suggestions')} · {t('copilot.suggestions.hint', { persona })}
          </Typography>
          <Stack spacing={0.5} sx={{ mt: 0.5 }}>
            {suggestions.map((question) => (
              <Chip
                key={question}
                size="small"
                variant="outlined"
                clickable
                label={question}
                onClick={() => void ask(question)}
                sx={{ justifyContent: 'flex-start', height: 'auto', py: 0.5, '& .MuiChip-label': { whiteSpace: 'normal' } }}
              />
            ))}
          </Stack>
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

import type { ShellContext } from '../types'
import { demoHeaders, fixturesOnly, resolveBffBaseUrl } from '../config'
import { HttpClient } from './httpClient'
import type { SingleEnvelope } from './envelope'

/** Reasoning tiers exposed in the composer; `auto` is resolved server-side. */
export type ReasoningTier = 'auto' | 'default' | 'high'

export type CopilotSourceKind = 'internal' | 'online' | 'glossary' | 'screen' | 'knowledge'

export interface CopilotSource {
  kind: CopilotSourceKind
  sourceId: string
  title: string
  snippet: string
  url?: string
  retrievedAt?: string
  offlineCorpus?: boolean
}

export interface CopilotMessage {
  messageId: string
  role: 'user' | 'assistant'
  content: string
  createdAt: string
  sources: CopilotSource[]
}

export interface CopilotAnswer {
  conversationId: string
  title: string
  language: string
  temporary: boolean
  persisted: boolean
  resolvedReasoning: 'default' | 'high'
  resolvedConcepts: string[]
  onlineSearchUsed: boolean
  question: CopilotMessage
  answer: CopilotMessage
}

export interface CopilotConversationSummary {
  conversationId: string
  title: string
  language: string
  createdAt: string
  updatedAt: string
  messageCount: number
  temporary: boolean
}

export interface CopilotConversation extends CopilotConversationSummary {
  messages: CopilotMessage[]
}

export interface GlossaryEntry {
  termId: string
  term: string
  definition: string
  language: string
  screens: string[]
}

export interface GlossaryOnlineResultItem {
  sourceId: string
  title: string
  snippet: string
  url: string
  published: string
}

export interface GlossaryOnlineResult {
  query: string
  language: string
  corpusLabel: string
  retrievedAt: string
  results: GlossaryOnlineResultItem[]
}

export interface CopilotSuggestions {
  section: string
  language: string
  questions: string[]
}

export interface CopilotScreenContext {
  section: string
  subView?: string
  site?: string
}

export interface CopilotChatRequest {
  question: string
  conversationId?: string
  locale?: string
  reasoning?: ReasoningTier
  onlineSearch?: boolean
  temporary?: boolean
  context?: CopilotScreenContext
}

/**
 * Offline copy used when the microfrontend is pinned to fixtures. It is
 * deliberately thin and honest: the dashboard still demonstrates the dock,
 * the composer and the glossary, but it never fabricates an answer that looks
 * as if it came from a grounded model.
 */
const OFFLINE_SUGGESTIONS = [
  'What am I looking at on this screen?',
  'Which metric should I act on first?',
  'Explain how thermal signature works.',
  'What is the difference between a target and measured evidence?',
  'What are the latest EU ETS announcements?',
]

function offlineAnswer(request: CopilotChatRequest, notice: string): CopilotAnswer {
  const now = new Date().toISOString()
  const conversationId = request.conversationId ?? `offline-${Date.now().toString(16)}`
  return {
    conversationId,
    title: request.question.slice(0, 60),
    language: (request.locale ?? 'en').slice(0, 2).toLowerCase(),
    temporary: true,
    persisted: false,
    resolvedReasoning: 'default',
    resolvedConcepts: [],
    onlineSearchUsed: false,
    question: {
      messageId: `offline-q-${now}`,
      role: 'user',
      content: request.question,
      createdAt: now,
      sources: [],
    },
    answer: {
      messageId: `offline-a-${now}`,
      role: 'assistant',
      content: notice,
      createdAt: now,
      sources: [],
    },
  }
}

/**
 * Thin client over the six `/v1/copilot/*` BFF endpoints. Unlike `DataClient`
 * it does not silently fall back to fixtures on error: a chat answer that
 * quietly degrades would be indistinguishable from a real one, so failures
 * surface to the caller and the panel shows a retry affordance.
 */
export class CopilotClient {
  private readonly http: HttpClient | null

  constructor(context: ShellContext) {
    this.http = fixturesOnly()
      ? null
      : new HttpClient({
          baseUrl: resolveBffBaseUrl(context),
          headers: demoHeaders(context),
          // Reasoning tiers think for longer than a dashboard query.
          timeoutMs: 30000,
        })
  }

  get isOffline(): boolean {
    return this.http === null
  }

  async suggestions(section: string, locale: string): Promise<CopilotSuggestions> {
    const language = (locale || 'en').slice(0, 2).toLowerCase()
    if (!this.http) {
      return { section, language, questions: OFFLINE_SUGGESTIONS }
    }
    const query = new URLSearchParams({ section, locale })
    const envelope = await this.http.getSingle<CopilotSuggestions>(
      `/v1/copilot/suggestions?${query.toString()}`,
    )
    return envelope.data
  }

  async glossary(
    query: string,
    locale: string,
    section?: string,
    limit = 8,
  ): Promise<GlossaryEntry[]> {
    if (!this.http) {
      return []
    }
    const params = new URLSearchParams({ locale, limit: String(limit) })
    if (query.trim()) {
      params.set('q', query.trim())
    }
    if (section) {
      params.set('section', section)
    }
    const envelope = await this.http.getSingle<{ entries: GlossaryEntry[] }>(
      `/v1/copilot/glossary?${params.toString()}`,
    )
    return envelope.data.entries
  }

  async conversations(): Promise<CopilotConversationSummary[]> {
    if (!this.http) {
      return []
    }
    const envelope = await this.http.getSingle<{
      conversations: CopilotConversationSummary[]
    }>('/v1/copilot/conversations')
    return envelope.data.conversations
  }

  async conversation(conversationId: string): Promise<CopilotConversation> {
    if (!this.http) {
      throw new Error('Conversation history is unavailable offline.')
    }
    const envelope = await this.http.getSingle<CopilotConversation>(
      `/v1/copilot/conversations/${encodeURIComponent(conversationId)}`,
    )
    return envelope.data
  }

  async deleteConversation(conversationId: string): Promise<void> {
    if (!this.http) {
      return
    }
    await this.http.del(`/v1/copilot/conversations/${encodeURIComponent(conversationId)}`)
  }

  async deleteAllConversations(): Promise<void> {
    if (!this.http) {
      return
    }
    await this.http.del('/v1/copilot/conversations')
  }

  async glossaryOnline(query: string, locale: string): Promise<GlossaryOnlineResult> {
    if (!this.http) {
      return { query, language: locale.slice(0, 2), corpusLabel: '', retrievedAt: '', results: [] }
    }
    const params = new URLSearchParams({ q: query.trim(), locale })
    const envelope = await this.http.getSingle<GlossaryOnlineResult>(
      `/v1/copilot/glossary/online?${params.toString()}`,
    )
    return envelope.data
  }

  async chat(request: CopilotChatRequest, offlineNotice: string): Promise<CopilotAnswer> {
    if (!this.http) {
      return offlineAnswer(request, offlineNotice)
    }
    const envelope = await this.http.post<SingleEnvelope<CopilotAnswer>>(
      '/v1/copilot/chat',
      request,
    )
    return envelope.data
  }
}

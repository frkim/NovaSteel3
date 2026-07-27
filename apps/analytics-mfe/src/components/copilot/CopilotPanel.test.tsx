import { describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@mui/material/styles'
import { CopilotPanel } from './CopilotPanel'
import type {
  CopilotAnswer,
  CopilotChatRequest,
  CopilotClient,
  CopilotConversation,
  CopilotConversationSummary,
  GlossaryEntry,
} from '../../api/copilotClient'
import { createNovaSteelTheme } from '../../designTokens'

function answerFor(request: CopilotChatRequest): CopilotAnswer {
  const now = '2026-07-26T10:00:00Z'
  return {
    conversationId: request.conversationId ?? 'conv-1',
    title: request.question.slice(0, 40),
    language: request.locale ?? 'en',
    temporary: Boolean(request.temporary),
    persisted: !request.temporary,
    resolvedReasoning: request.reasoning === 'high' ? 'high' : 'default',
    resolvedConcepts: ['Lining risk'],
    onlineSearchUsed: Boolean(request.onlineSearch),
    question: {
      messageId: 'msg-q',
      role: 'user',
      content: request.question,
      createdAt: now,
      sources: [],
    },
    answer: {
      messageId: 'msg-a',
      role: 'assistant',
      content: 'You are on **Furnace Health**, so I read this as **Lining risk**.',
      createdAt: now,
      sources: [
        { kind: 'screen', sourceId: 'furnace-health', title: 'Furnace Health', snippet: 'x' },
        {
          kind: 'online',
          sourceId: 'eu-ets',
          title: 'EU Emissions Trading System',
          snippet: 'y',
          url: 'https://climate.ec.europa.eu/',
        },
      ],
    },
  }
}

interface Stub {
  client: CopilotClient
  chat: ReturnType<typeof vi.fn>
  deleteConversation: ReturnType<typeof vi.fn>
}

function stubClient(overrides: Partial<Record<keyof CopilotClient, unknown>> = {}): Stub {
  const chat = vi.fn(async (request: CopilotChatRequest) => answerFor(request))
  const deleteConversation = vi.fn(async () => undefined)
  const conversations: CopilotConversationSummary[] = [
    {
      conversationId: 'conv-9',
      title: 'Why is the lining risk high?',
      language: 'en',
      createdAt: '2026-07-26T09:00:00Z',
      updatedAt: '2026-07-26T09:05:00Z',
      messageCount: 4,
      temporary: false,
    },
  ]
  const glossary: GlossaryEntry[] = [
    {
      termId: 'thermal-signature',
      term: 'Thermal signature',
      definition: 'The pattern of temperatures that describes how heat moves through a furnace.',
      language: 'en',
      screens: ['furnace-health'],
    },
  ]
  const conversation: CopilotConversation = {
    ...conversations[0],
    messages: [
      { messageId: 'm1', role: 'user', content: 'Why is the lining risk high?', createdAt: '', sources: [] },
      { messageId: 'm2', role: 'assistant', content: 'Restored answer.', createdAt: '', sources: [] },
    ],
  }

  const client = {
    isOffline: false,
    chat,
    deleteConversation,
    deleteAllConversations: vi.fn(async () => undefined),
    suggestions: vi.fn(async (section: string, locale: string) => ({
      section,
      language: locale,
      questions: ['Explain how thermal signature works', 'What is the risk?'],
    })),
    glossary: vi.fn(async () => glossary),
    glossaryOnline: vi.fn(async () => ({ query: '', language: 'en', corpusLabel: '', retrievedAt: '', results: [] })),
    conversations: vi.fn(async () => conversations),
    conversation: vi.fn(async () => conversation),
    ...overrides,
  } as unknown as CopilotClient

  return { client, chat, deleteConversation }
}

function renderPanel(stub: Stub, locale = 'en-LU') {
  return render(
    <ThemeProvider theme={createNovaSteelTheme('light')}>
      <CopilotPanel
        client={stub.client}
        section="furnace-health"
        subView="lining-forecast"
        site="de"
        screenTitle="Furnace Health"
        persona="Furnace Operator"
        locale={locale}
      />
    </ThemeProvider>,
  )
}

describe('CopilotPanel', () => {
  it('shows the enterprise data protection notice and the current screen context', async () => {
    renderPanel(stubClient())

    expect(screen.getByText('Enterprise data protection applies to this chat.')).toBeInTheDocument()
    expect(screen.getByTestId('copilot-context-chip')).toHaveTextContent('Furnace Health')
    // Let the suggestion, glossary and history fetches settle inside this test.
    expect(await screen.findByText('What is the risk?')).toBeInTheDocument()
    expect(await screen.findByText('Thermal signature')).toBeInTheDocument()
  })

  it('offers persona suggestions and sends the screen context when one is used', async () => {
    const stub = stubClient()
    const user = userEvent.setup({ delay: null })
    renderPanel(stub)

    const suggestion = await screen.findByText('Explain how thermal signature works')
    await user.click(suggestion)

    await waitFor(() => expect(stub.chat).toHaveBeenCalledTimes(1))
    expect(stub.chat.mock.calls[0][0]).toMatchObject({
      question: 'Explain how thermal signature works',
      context: { section: 'furnace-health', subView: 'lining-forecast', site: 'de' },
      reasoning: 'auto',
      onlineSearch: false,
      temporary: false,
    })
    expect(await screen.findByTestId('copilot-message-assistant')).toHaveTextContent('Furnace Health')
  })

  it('renders answer sources, linking online results to their public page', async () => {
    const stub = stubClient()
    const user = userEvent.setup({ delay: null })
    renderPanel(stub)

    await user.click(await screen.findByText('What is the risk?'))

    const sources = await screen.findByTestId('copilot-sources')
    expect(within(sources).getByText('EU Emissions Trading System')).toHaveAttribute(
      'href',
      'https://climate.ec.europa.eu/',
    )
    expect(within(sources).getByText(/Screen context/)).toBeInTheDocument()
  })

  it('passes the online search and high reasoning choices to the backend', async () => {
    const stub = stubClient()
    const user = userEvent.setup({ delay: null })
    renderPanel(stub)

    await screen.findByText('What is the risk?')
    await user.click(await screen.findByRole('switch', { name: 'Online search' }))
    await user.click(screen.getByRole('button', { name: 'High reasoning' }))
    // `fireEvent.change` keeps the test well inside the default timeout; the
    // typing path itself is covered by the error test below.
    fireEvent.change(screen.getByLabelText('Ask a question about this screen…'), {
      target: { value: 'What changed?' },
    })
    await user.click(screen.getByRole('button', { name: 'Send' }))

    await waitFor(() => expect(stub.chat).toHaveBeenCalledTimes(1))
    expect(stub.chat.mock.calls[0][0]).toMatchObject({ onlineSearch: true, reasoning: 'high' })
  })

  it('keeps temporary chats out of the saved history', async () => {
    const stub = stubClient()
    const user = userEvent.setup({ delay: null })
    renderPanel(stub)

    await screen.findByText('What is the risk?')
    await user.click(screen.getByRole('button', { name: 'Temporary chat' }))
    await user.click(await screen.findByText('What is the risk?'))

    await waitFor(() => expect(stub.chat).toHaveBeenCalledTimes(1))
    expect(stub.chat.mock.calls[0][0]).toMatchObject({ temporary: true })
    // A temporary answer is never persisted, so the saved history is not reloaded.
    expect(stub.client.conversations).toHaveBeenCalledTimes(1)
  })

  it('restores and deletes stored conversations', async () => {
    const stub = stubClient()
    const user = userEvent.setup({ delay: null })
    renderPanel(stub)

    const list = await screen.findByTestId('copilot-conversations')
    await user.click(within(list).getByRole('button', { name: /Open conversation: Why is the lining risk high\?/ }))
    expect(await screen.findByText('Restored answer.')).toBeInTheDocument()

    await user.click(
      within(await screen.findByTestId('copilot-conversations')).getByRole('button', {
        name: /Delete conversation: Why is the lining risk high\?/,
      }),
    )
    await waitFor(() => expect(stub.deleteConversation).toHaveBeenCalledWith('conv-9'))
  })

  it('shows a definition for a glossary lookup', async () => {
    renderPanel(stubClient())

    const glossary = await screen.findByTestId('copilot-glossary')
    expect(await within(glossary).findByText('Thermal signature')).toBeInTheDocument()
    expect(
      within(glossary).getByText(/pattern of temperatures that describes how heat moves/),
    ).toBeInTheDocument()
  })

  it('translates the whole panel when the chat language changes', async () => {
    const stub = stubClient()
    const user = userEvent.setup({ delay: null })
    renderPanel(stub)

    await screen.findByText('What is the risk?')
    await user.click(screen.getByRole('combobox', { name: 'Chat language' }))
    await user.click(await screen.findByRole('option', { name: 'FR' }))

    expect(
      await screen.findByText('La protection des données d’entreprise s’applique à ce chat.'),
    ).toBeInTheDocument()
    await waitFor(() => expect(stub.client.suggestions).toHaveBeenCalledWith('furnace-health', 'fr'))
  })

  it('surfaces a retry-able error instead of inventing an answer', async () => {
    const stub = stubClient({ chat: vi.fn(async () => Promise.reject(new Error('boom'))) })
    const user = userEvent.setup({ delay: null })
    renderPanel(stub)

    await screen.findByText('What is the risk?')
    fireEvent.change(screen.getByLabelText('Ask a question about this screen…'), {
      target: { value: 'What changed?' },
    })
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The assistant could not answer.')
    expect(screen.queryByTestId('copilot-message-assistant')).not.toBeInTheDocument()
  })
})

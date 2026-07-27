import { useState } from 'react'
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined'
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep'
import HistoryIcon from '@mui/icons-material/History'
import type { CopilotConversationSummary } from '../../api/copilotClient'
import type { TranslateFn } from '../../i18n/messages'

interface ConversationListProps {
  conversations: CopilotConversationSummary[]
  activeId: string | null
  onOpen: (conversationId: string) => void
  onDelete: (conversationId: string) => void
  onDeleteAll?: () => void
  t: TranslateFn
}

export function ConversationList({
  conversations,
  activeId,
  onOpen,
  onDelete,
  onDeleteAll,
  t,
}: ConversationListProps) {
  const [confirmOpen, setConfirmOpen] = useState(false)

  return (
    <Box data-testid="copilot-conversations">
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 0.5 }}>
        <HistoryIcon fontSize="small" color="action" />
        <Typography variant="subtitle2">{t('copilot.conversations')}</Typography>
        <Box sx={{ flexGrow: 1 }} />
        {onDeleteAll && conversations.length > 0 && (
          <Tooltip title={t('copilot.conversations.deleteAll')}>
            <IconButton
              size="small"
              aria-label={t('copilot.conversations.deleteAll')}
              data-testid="copilot-delete-all"
              onClick={() => setConfirmOpen(true)}
            >
              <DeleteSweepIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Stack>
      {conversations.length === 0 ? (
        <Typography variant="caption" color="text.secondary">
          {t('copilot.conversations.empty')}
        </Typography>
      ) : (
        <List dense disablePadding>
          {conversations.map((conversation) => (
            <ListItemButton
              key={conversation.conversationId}
              selected={conversation.conversationId === activeId}
              data-testid="copilot-conversation"
              onClick={() => onOpen(conversation.conversationId)}
              aria-label={`${t('copilot.conversations.restore')}: ${conversation.title}`}
              sx={{ borderRadius: 1, pr: 5 }}
            >
              <ListItemText
                primary={conversation.title}
                secondary={t('table.rows', {
                  from: 1,
                  to: conversation.messageCount,
                  total: conversation.messageCount,
                })}
                slotProps={{
                  primary: { variant: 'body2', noWrap: true },
                  secondary: { variant: 'caption' },
                }}
              />
              <Tooltip title={t('copilot.conversations.delete')}>
                <IconButton
                  size="small"
                  edge="end"
                  aria-label={`${t('copilot.conversations.delete')}: ${conversation.title}`}
                  sx={{ position: 'absolute', right: 4 }}
                  onClick={(event) => {
                    event.stopPropagation()
                    onDelete(conversation.conversationId)
                  }}
                >
                  <DeleteOutlineIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </ListItemButton>
          ))}
        </List>
      )}
      <Dialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        aria-labelledby="delete-all-title"
      >
        <DialogContent>
          <DialogContentText id="delete-all-title">
            {t('copilot.conversations.deleteAll.confirm')}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmOpen(false)} size="small">
            {t('copilot.conversations.deleteAll.no')}
          </Button>
          <Button
            onClick={() => {
              setConfirmOpen(false)
              onDeleteAll?.()
            }}
            color="error"
            size="small"
            data-testid="copilot-delete-all-confirm"
          >
            {t('copilot.conversations.deleteAll.yes')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

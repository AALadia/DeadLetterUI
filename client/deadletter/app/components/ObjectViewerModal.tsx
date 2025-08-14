// ObjectViewerModal.tsx
import * as React from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Typography,
  Button,
  Stack,
  Box,
  Divider,
  Tooltip,
  TextField,
  Chip,
} from "@mui/material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CloseIcon from "@mui/icons-material/Close";

type JSONValue =
  | string
  | number
  | boolean
  | null
  | JSONValue[]
  | { [key: string]: JSONValue };

export interface ObjectViewerModalProps {
  open: boolean;
  onClose: () => void;
  data: Record<string, JSONValue>;
  title?: string;
  maxWidth?: "xs" | "sm" | "md" | "lg" | "xl";
  dense?: boolean; // tighter spacing if you want
}

const typeLabel = (value: JSONValue) => {
  const t = Array.isArray(value) ? "array" : value === null ? "null" : typeof value;
  return t;
};

const formatValue = (value: JSONValue) => {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean" || value === null)
    return String(value);
  // objects/arrays -> pretty JSON single-line fallback
  try {
    return JSON.stringify(value);
  } catch {
    return "[Unserializable]";
  }
};

const isPlainObject = (v: JSONValue): v is Record<string, JSONValue> =>
  !!v && typeof v === "object" && !Array.isArray(v);

const CopyButton: React.FC<{ getText: () => string; size?: "small" | "medium" }> = ({
  getText,
  size = "small",
}) => {
  const [copied, setCopied] = React.useState(false);
  return (
    <Tooltip title={copied ? "Copied!" : "Copy"}>
      <IconButton
        size={size}
        onClick={async (e) => {
          e.stopPropagation();
          try {
            await navigator.clipboard.writeText(getText());
            setCopied(true);
            setTimeout(() => setCopied(false), 1200);
          } catch {
            // no-op
          }
        }}
      >
        <ContentCopyIcon fontSize="inherit" />
      </IconButton>
    </Tooltip>
  );
};

const Row: React.FC<{
  k: string;
  v: JSONValue;
  level?: number;
  dense?: boolean;
  filter?: string;
}> = ({ k, v, level = 0, dense = false, filter }) => {
  const indent = level * 16;
  const matchesFilter = (txt: string) =>
    !filter ||
    txt.toLowerCase().includes(filter.toLowerCase());

  const selfText = `${k}: ${formatValue(v)}`;
  if (!matchesFilter(k) && !matchesFilter(formatValue(v)) && !matchesFilter(typeLabel(v))) {
    // If neither key/value/type matches filter, hide this row AND its children.
    if (!isPlainObject(v) && !Array.isArray(v)) return null;
  }

  const spacingY = dense ? 1 : 1.25;

  if (isPlainObject(v)) {
    const keys = Object.keys(v);
    return (
      <Stack spacing={0.75} sx={{ pl: `${indent}px` }}>
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          sx={{ py: spacingY }}
        >
          <Stack direction="row" spacing={1} alignItems="center" sx={{ minWidth: 0 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              {k}
            </Typography>
            <Chip label="object" size="small" />
            <Typography variant="caption" color="text.secondary">
              {keys.length} {keys.length === 1 ? "field" : "fields"}
            </Typography>
          </Stack>
          <CopyButton getText={() => JSON.stringify(v, null, 2)} />
        </Stack>
        <Divider />
        <Stack spacing={0} sx={{ mt: 0.5 }}>
          {keys.map((ck) => (
            <Row key={ck} k={ck} v={v[ck]} level={level + 1} dense={dense} filter={filter} />
          ))}
        </Stack>
      </Stack>
    );
  }

  if (Array.isArray(v)) {
    return (
      <Stack spacing={0.75} sx={{ pl: `${indent}px` }}>
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          sx={{ py: spacingY }}
        >
          <Stack direction="row" spacing={1} alignItems="center" sx={{ minWidth: 0 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              {k}
            </Typography>
            <Chip label="array" size="small" />
            <Typography variant="caption" color="text.secondary">
              {v.length} {v.length === 1 ? "item" : "items"}
            </Typography>
          </Stack>
          <CopyButton getText={() => JSON.stringify(v, null, 2)} />
        </Stack>
        <Divider />
        <Stack spacing={0} sx={{ mt: 0.5 }}>
          {v.map((item, idx) => (
            <Row
              key={idx}
              k={`${idx}`}
              v={item as JSONValue}
              level={level + 1}
              dense={dense}
              filter={filter}
            />
          ))}
        </Stack>
      </Stack>
    );
  }

  return (
    <Stack
      direction="row"
      alignItems="flex-start"
      justifyContent="space-between"
      sx={{ pl: `${indent}px`, py: dense ? 0.75 : 1.25 }}
    >
      <Stack spacing={0.25} sx={{ minWidth: 0 }}>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ minWidth: 0 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, flexShrink: 0 }}>
            {k}
          </Typography>
          <Chip label={typeLabel(v)} size="small" />
        </Stack>
        <Box
          sx={{
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            fontSize: 13,
            color: "text.secondary",
            wordBreak: "break-word",
            whiteSpace: "pre-wrap",
            maxWidth: "100%",
          }}
        >
          {formatValue(v)}
        </Box>
      </Stack>
      <CopyButton getText={() => formatValue(v)} />
    </Stack>
  );
};

export const ObjectViewerModal: React.FC<ObjectViewerModalProps> = ({
  open,
  onClose,
  data,
  title = "Object Viewer",
  maxWidth = "md",
  dense = false,
}) => {
  const [filter, setFilter] = React.useState("");
  const pretty = React.useMemo(() => JSON.stringify(data, null, 2), [data]);


  if (!data) {
    return null
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth={maxWidth}>
      <DialogTitle sx={{ pr: 6 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">{title}</Typography>
          <Stack direction="row" spacing={1} alignItems="center">
            <Tooltip title="Copy entire JSON">
              <span>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={async () => {
                    await navigator.clipboard.writeText(pretty);
                  }}
                >
                  Copy JSON
                </Button>
              </span>
            </Tooltip>
            <Tooltip title="Close">
              <IconButton onClick={onClose}>
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        </Stack>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 2 }}>
        <Stack spacing={2}>
          <TextField
            size="small"
            placeholder="Filter by key, value, or type…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />

          <Box
            sx={{
              borderRadius: 2,
              border: (theme) => `1px solid ${theme.palette.divider}`,
              p: dense ? 1 : 2,
            }}
          >
            {/* Top-level rows */}
            <Stack spacing={0}>
              {Object.keys(data).length === 0 ? (
                <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
                  (empty object)
                </Typography>
              ) : (
                Object.entries(data).map(([k, v]) => (
                  <Row key={k} k={k} v={v} dense={dense} filter={filter} />
                ))
              )}
            </Stack>
          </Box>

          {/* Raw JSON viewer */}
          <Box
            sx={{
              borderRadius: 2,
              border: (theme) => `1px solid ${theme.palette.divider}`,
              bgcolor: "background.default",
              p: 2,
            }}
          >
            <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                Raw JSON
              </Typography>
              <CopyButton getText={() => pretty} />
            </Stack>
            <Box
              component="pre"
              sx={{
                m: 0,
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                fontSize: 12.5,
                overflow: "auto",
                maxHeight: 320,
              }}
            >
              {pretty}
            </Box>
          </Box>
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 2, py: 1.5 }}>
        <Button onClick={onClose} variant="contained">
            Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Example usage
/*
import React from "react";
import { ObjectViewerModal } from "./ObjectViewerModal";
import { Button } from "@mui/material";

export default function Demo() {
  const [open, setOpen] = React.useState(false);
  const sample = {
    id: 123,
    name: "Vince",
    flags: { active: true, beta: false },
    tags: ["alpha", "bravo", "charlie"],
    notes: null,
  };
  return (
    <>
      <Button onClick={() => setOpen(true)}>Open Viewer</Button>
      <ObjectViewerModal
        open={open}
        onClose={() => setOpen(false)}
        data={sample}
        title="Sample Object"
        maxWidth="md"
        dense={false}
      />
    </>
  );
}
*/


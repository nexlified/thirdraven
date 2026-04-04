import { FormEvent, useEffect, useRef, useState } from "react";
import { quickAddTransaction, type TransactionPublic } from "../api/transactions";

interface QuickAddTransactionProps {
  defaultCurrency?: string;
  onSuccess?: (tx: TransactionPublic) => void;
  placeholder?: string;
}

export default function QuickAddTransaction({
  defaultCurrency = "INR",
  onSuccess,
  placeholder,
}: QuickAddTransactionProps) {
  const [input, setInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const successTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (successTimeoutRef.current !== null) {
        window.clearTimeout(successTimeoutRef.current);
      }
    };
  }, []);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || submitting) {
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const tx = await quickAddTransaction(trimmed, defaultCurrency);
      const symbol = tx.transaction_type === "income" ? "+" : "-";
      const category = tx.category?.name ?? "";
      setSuccessMsg(
        `${symbol} ${tx.currency} ${tx.amount.toFixed(0)}${category ? ` - ${category}` : ""}`
      );
      setInput("");
      onSuccess?.(tx);

      if (successTimeoutRef.current !== null) {
        window.clearTimeout(successTimeoutRef.current);
      }
      successTimeoutRef.current = window.setTimeout(() => {
        setSuccessMsg(null);
        successTimeoutRef.current = null;
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add transaction");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="quick-add-transaction">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          className="quick-add-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder ?? 'Try: "500 fuel" or "salary 50000"'}
          aria-label="Quick add transaction"
          disabled={submitting}
        />
        <button
          type="submit"
          className="btn-primary"
          disabled={!input.trim() || submitting}
        >
          {submitting ? "Adding..." : "Add"}
        </button>
      </form>

      {successMsg && <span className="quick-add-success">{successMsg}</span>}
      {error && <span className="form-error">{error}</span>}
    </div>
  );
}


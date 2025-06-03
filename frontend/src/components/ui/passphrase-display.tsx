import React, { useMemo } from 'react';
import { Button } from './button';
import { Copy, Check, Clipboard } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

interface PassphraseDisplayProps {
  passphrase: string;
  showCopyButton?: boolean;
  className?: string;
}

// Color palette with good visibility (not too dark, not too light)
const WORD_COLORS = [
  'text-red-500',
  'text-blue-500', 
  'text-green-500',
  'text-purple-500',
  'text-pink-500',
  'text-indigo-500',
  'text-teal-500',
  'text-orange-500',
  'text-cyan-500',
  'text-emerald-500',
  'text-violet-500',
  'text-fuchsia-500',
  'text-rose-500',
  'text-amber-500',
  'text-lime-500',
  'text-sky-500'
];

export function PassphraseDisplay({ 
  passphrase, 
  showCopyButton = false, 
  className = '' 
}: PassphraseDisplayProps) {
  const [copied, setCopied] = useState(false);
  
  // Split passphrase into words and assign random colors
  const coloredWords = useMemo(() => {
    const words = passphrase.split('-');
    return words.map((word, index) => ({
      word,
      color: WORD_COLORS[index % WORD_COLORS.length]
    }));
  }, [passphrase]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(passphrase);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy passphrase:', err);
    }
  };

  return (
    <div className={`relative space-y-3 ${className}`}>
      <div className={cn(
          "file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground dark:bg-input/30 border-input flex h-10 w-full min-w-0 rounded-md border bg-transparent px-3 py-1 text-base shadow-xs transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm items-center",
          "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
          "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
          
        )}>
          {coloredWords.map((item, index) => (
            <React.Fragment key={index}>
              <span className={item.color}>{item.word}</span>
              {index < coloredWords.length - 1 && (
                <span className="text-muted-foreground mx-1">-</span>
              )}
            </React.Fragment>
          ))}
      </div>
      
      {showCopyButton && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleCopy}
          className="absolute right-1 top-1 rounded-sm"
        >
          {copied ? (
            <>
              <Check className="h-4 w-4" />
            </>
          ) : (
            <>
              <Clipboard className="h-4 w-4" />
            </>
          )}
        </Button>
      )}
    </div>
  );
} 
import type { TransactionInfoResponse } from '@/models/transaction.ts';
import { TransactionType } from '@/core/transaction.ts';

export interface BillDef {
    day: number;
    name: string;
    amountCents: number;
    account: string;
    category: string;
}

export interface PendingBill extends BillDef {
    daysUntil: number;
    dueDate: Date;
}

export interface CycleRange {
    start: Date;
    end: Date;
    nextPayday: Date;
    totalDays: number;
    currentDay: number;
    daysRemaining: number;
}

export const STATIC_MONTHLY_BILLS: BillDef[] = [
    { day: 1,  name: 'Canone Conto Intesa',   amountCents: 700,    account: 'Intesa',           category: 'Finanza -> Costi di servizio' },
    { day: 2,  name: 'Affitto (Rent)',         amountCents: 50000,  account: 'Budget Settimana', category: 'Alloggio -> Affitto e Mutuo' },
    { day: 5,  name: 'Finanziamento PC',       amountCents: 3673,   account: 'Intesa',           category: 'Alloggio -> Elettronica' },
    { day: 5,  name: 'IONOS Spazio Web',       amountCents: 1098,   account: 'Budget Settimana', category: 'Comunicazione -> Internet' },
    { day: 8,  name: 'Fibra Casa (Internet)',  amountCents: 2979,   account: 'Intesa',           category: 'Comunicazione -> Internet' },
    { day: 8,  name: 'Amazon Prime Ad-Free',   amountCents: 199,    account: 'Budget Settimana', category: 'Intrattenimento -> Sub' },
    { day: 15, name: 'Tariffa Mobile (TIM)',   amountCents: 799,    account: 'Intesa',           category: 'Comunicazione -> Telefono' },
    { day: 16, name: 'Amazon Prime',           amountCents: 499,    account: 'Budget Settimana', category: 'Intrattenimento -> Sub' },
    { day: 16, name: 'PAC Trade Investiti',    amountCents: 5000,   account: 'Trade Republic',   category: 'Trasferimento -> PAC' },
    { day: 20, name: 'Rata Auto',              amountCents: 30450,  account: 'Intesa',           category: 'Trasporti -> Spese auto' },
    { day: 21, name: 'Utenze (Luce & Gas)',    amountCents: 11734,  account: 'Intesa',           category: 'Utenze -> Luce e Gas' },
    { day: 30, name: 'IONOS VPS',              amountCents: 976,    account: 'Budget Settimana', category: 'Comunicazione -> VPS' }
];

export const FIXED_KEYWORDS = [
    'affitto', 'mutuo', 'elettronica', 'spese auto', 'utenze',
    'internet', 'telefono', 'servizio', 'bollette', 'tasse',
    'viaggi', 'biglietti aerei', 'pac trade', 'vps'
];

export function getPayday(year: number, month: number): Date {
    const d = new Date(year, month, 28, 0, 0, 0, 0);
    while (d.getDay() === 0 || d.getDay() === 6) { // 0 = Sunday, 6 = Saturday
        d.setDate(d.getDate() + 1);
    }
    return d;
}

export function isDatePayday(d: Date): boolean {
    const pd = getPayday(d.getFullYear(), d.getMonth());
    return pd.getFullYear() === d.getFullYear() &&
           pd.getMonth() === d.getMonth() &&
           pd.getDate() === d.getDate();
}

export function computeCycle(targetDate: Date): CycleRange {
    const year = targetDate.getFullYear();
    const month = targetDate.getMonth();

    const thisMonthPayday = getPayday(year, month);
    let start: Date;
    let nextPayday: Date;

    if (targetDate.getTime() >= thisMonthPayday.getTime()) {
        start = thisMonthPayday;
        nextPayday = getPayday(year, month + 1);
    } else {
        nextPayday = thisMonthPayday;
        start = getPayday(year, month - 1);
    }

    const end = new Date(nextPayday.getFullYear(), nextPayday.getMonth(), nextPayday.getDate() - 1, 23, 59, 59, 999);
    const totalDays = Math.round((new Date(end.getFullYear(), end.getMonth(), end.getDate()).getTime() - new Date(start.getFullYear(), start.getMonth(), start.getDate()).getTime()) / (1000 * 60 * 60 * 24)) + 1;
    const currentDay = Math.min(totalDays, Math.max(1, Math.round((new Date(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate()).getTime() - new Date(start.getFullYear(), start.getMonth(), start.getDate()).getTime()) / (1000 * 60 * 60 * 24)) + 1));
    const daysRemaining = Math.max(1, Math.round((new Date(nextPayday.getFullYear(), nextPayday.getMonth(), nextPayday.getDate()).getTime() - new Date(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate()).getTime()) / (1000 * 60 * 60 * 24)));

    return { start, end, nextPayday, totalDays, currentDay, daysRemaining };
}

export function isFixedOrTravel(
    tx: TransactionInfoResponse,
    fixedFilter: Record<string, boolean> | undefined,
    categoriesMap: Record<string, { name?: string; parentId?: string }>
): boolean {
    if (fixedFilter && tx.categoryId && fixedFilter[tx.categoryId]) {
        return true;
    }

    const cat = categoriesMap[tx.categoryId];
    const catName = (cat?.name || '').toLowerCase();
    const parentCat = cat?.parentId ? categoriesMap[cat.parentId] : null;
    const parentCatName = (parentCat?.name || '').toLowerCase();
    const comment = (tx.comment || '').toLowerCase();

    if (fixedFilter && cat?.parentId && fixedFilter[cat.parentId]) {
        return true;
    }

    for (const kw of FIXED_KEYWORDS) {
        if (catName.includes(kw) || parentCatName.includes(kw) || comment.includes(kw)) {
            return true;
        }
    }

    return false;
}

export function getPaidBillsInCycle(
    cycleTransactions: TransactionInfoResponse[],
    fixedFilter: Record<string, boolean> | undefined,
    categoriesMap: Record<string, { name?: string; parentId?: string }>
): Set<string> {
    const paidSet = new Set<string>();
    const fixedExpenses = cycleTransactions.filter(
        t => t.type === TransactionType.Expense && isFixedOrTravel(t, fixedFilter, categoriesMap)
    );

    for (const bill of STATIC_MONTHLY_BILLS) {
        for (const tx of fixedExpenses) {
            const txDate = new Date(tx.time * 1000);
            const amtDiff = Math.abs((tx.sourceAmount || 0) - bill.amountCents);
            const dayDiff = Math.abs(txDate.getDate() - bill.day);

            if (dayDiff <= 3 && amtDiff <= 200) {
                paidSet.add(bill.name);
                break;
            }

            const cat = categoriesMap[tx.categoryId];
            const catName = (cat?.name || '').toLowerCase();
            const comment = (tx.comment || '').toLowerCase();

            if (bill.name === 'Canone Conto Intesa' && (catName.includes('servizio') || comment.includes('canone'))) {
                paidSet.add(bill.name);
                break;
            }
            if (bill.name === 'Affitto (Rent)' && (catName.includes('affitto') || comment.includes('affitto'))) {
                paidSet.add(bill.name);
                break;
            }
            if (bill.name === 'Finanziamento PC' && amtDiff === 0) {
                paidSet.add(bill.name);
                break;
            }
            if (bill.name === 'IONOS Spazio Web' && amtDiff === 0) {
                paidSet.add(bill.name);
                break;
            }
            if (bill.name === 'IONOS VPS' && (comment.includes('vps') || (amtDiff === 0 && dayDiff <= 4))) {
                paidSet.add(bill.name);
                break;
            }
        }
    }

    return paidSet;
}

export function getPendingBills(
    paidBills: Set<string>,
    nextPayday: Date,
    today: Date
): PendingBill[] {
    const list: PendingBill[] = [];
    const todayMidnight = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0, 0, 0);

    for (const bill of STATIC_MONTHLY_BILLS) {
        if (paidBills.has(bill.name)) {
            continue;
        }

        const thisMonthDue = new Date(today.getFullYear(), today.getMonth(), bill.day, 0, 0, 0, 0);
        if (thisMonthDue.getTime() >= todayMidnight.getTime() && thisMonthDue.getTime() < nextPayday.getTime()) {
            const daysUntil = Math.round((thisMonthDue.getTime() - todayMidnight.getTime()) / (1000 * 60 * 60 * 24));
            list.push({ ...bill, daysUntil, dueDate: thisMonthDue });
            continue;
        }

        const nextMonthDue = new Date(today.getFullYear(), today.getMonth() + 1, bill.day, 0, 0, 0, 0);
        if (nextMonthDue.getTime() >= todayMidnight.getTime() && nextMonthDue.getTime() < nextPayday.getTime()) {
            const daysUntil = Math.round((nextMonthDue.getTime() - todayMidnight.getTime()) / (1000 * 60 * 60 * 24));
            list.push({ ...bill, daysUntil, dueDate: nextMonthDue });
        }
    }

    return list.sort((a, b) => a.daysUntil - b.daysUntil);
}

export function getCycleSalary(
    cycleTransactions: TransactionInfoResponse[],
    priorCycleTransactions: TransactionInfoResponse[],
    cycleStart: Date
): number {
    const cycleStartTs = Math.floor(cycleStart.getTime() / 1000);
    const windowStartTs = cycleStartTs - (4 * 24 * 3600);

    const candidates = cycleTransactions
        .concat(priorCycleTransactions.filter(t => t.time >= windowStartTs))
        .filter(t => t.type === TransactionType.Income && (t.sourceAmount || 0) >= 100000);

    if (candidates.length > 0 && candidates[0]) {
        let highest = candidates[0];
        for (const c of candidates) {
            if (c.sourceAmount > highest.sourceAmount) {
                highest = c;
            }
        }
        return highest.sourceAmount;
    }

    return 173600; // 1,736.00 EUR fallback
}

export function getCycleDailyVariableSpending(
    cycleTransactions: TransactionInfoResponse[],
    cycleRange: CycleRange,
    fixedFilter: Record<string, boolean> | undefined,
    categoriesMap: Record<string, { name?: string; parentId?: string }>
): { dailySpend: number[]; cumulativeSpend: number[] } {
    const days = cycleRange.totalDays;
    const startDate = cycleRange.start;
    const dailySpend: number[] = new Array(days + 1).fill(0);

    const varTxs = cycleTransactions.filter(
        t => t.type === TransactionType.Expense && !isFixedOrTravel(t, fixedFilter, categoriesMap)
    );

    for (const tx of varTxs) {
        const txDate = new Date(tx.time * 1000);
        const txMidnight = new Date(txDate.getFullYear(), txDate.getMonth(), txDate.getDate()).getTime();
        const startMidnight = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate()).getTime();
        const dayIdx = Math.round((txMidnight - startMidnight) / (1000 * 60 * 60 * 24)) + 1;

        if (dayIdx >= 1 && dayIdx <= days) {
            dailySpend[dayIdx] = (dailySpend[dayIdx] ?? 0) + (tx.sourceAmount || 0);
        }
    }

    const cumulativeSpend: number[] = new Array(days + 1).fill(0);
    for (let i = 1; i <= days; i++) {
        cumulativeSpend[i] = (cumulativeSpend[i - 1] ?? 0) + (dailySpend[i] ?? 0);
    }

    return { dailySpend, cumulativeSpend };
}

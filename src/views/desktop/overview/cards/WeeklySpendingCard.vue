<template>
    <v-card :class="{ 'disabled': disabled }">
        <template #title>
            <div class="d-flex align-center">
                <span>{{ tt('Weekly Spending Breakdown') }}</span>
                <span class="text-body-2 ms-3">{{ monthDisplayName }}</span>
            </div>
        </template>

        <v-card-text v-if="!loading && !rows.length">
            <span class="text-body-1">{{ tt('No transaction data') }}</span>
        </v-card-text>

        <v-table class="weekly-spending-table text-no-wrap" density="comfortable" v-else>
            <thead>
                <tr>
                    <th>{{ tt('Category') }}</th>
                    <th class="text-end" :class="{ 'weekly-spending-current-week': weekIdx === currentWeekIndex }"
                        :key="weekIdx" v-for="(week, weekIdx) in weekRanges">{{ getWeekDisplayName(week) }}</th>
                    <th class="text-end font-weight-bold">{{ tt('Month Total') }}</th>
                </tr>
            </thead>
            <tbody v-if="loading && !rows.length">
                <tr :key="idx" v-for="idx in 5">
                    <td :key="colIdx" v-for="colIdx in (weekRanges.length + 2)">
                        <v-skeleton-loader class="skeleton-no-margin my-2" type="text" :loading="true"></v-skeleton-loader>
                    </td>
                </tr>
            </tbody>
            <tbody v-else>
                <tr :key="row.categoryId" v-for="row in rows">
                    <td>{{ row.categoryName }}</td>
                    <td class="text-end" :class="{ 'weekly-spending-current-week': weekIdx === currentWeekIndex }"
                        :key="weekIdx" v-for="(weekAmount, weekIdx) in row.weekAmounts">
                        <router-link class="weekly-spending-cell-link" :to="getCellDetailsLink(row.categoryId, weekIdx)"
                                     v-if="weekAmount !== 0 && showAmountInHomePage">{{ getDisplayAmount(weekAmount) }}</router-link>
                        <span v-else-if="weekAmount !== 0">{{ getDisplayAmount(weekAmount) }}</span>
                        <span class="text-disabled" v-else>-</span>
                    </td>
                    <td class="text-end font-weight-medium">{{ getDisplayAmount(row.totalAmount, row.incomplete) }}</td>
                </tr>
                <tr class="weekly-spending-total-row">
                    <td class="font-weight-bold">{{ tt('Total') }}</td>
                    <td class="text-end font-weight-medium" :class="{ 'weekly-spending-current-week': weekIdx === currentWeekIndex }"
                        :key="weekIdx" v-for="(weekTotal, weekIdx) in weekTotals">{{ getDisplayAmount(weekTotal) }}</td>
                    <td class="text-end font-weight-bold">{{ getDisplayAmount(grandTotal, grandTotalIncomplete) }}</td>
                </tr>
            </tbody>
        </v-table>
    </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { useI18n } from '@/locales/helpers.ts';

import { useSettingsStore } from '@/stores/setting.ts';
import { useUserStore } from '@/stores/user.ts';
import { useAccountsStore } from '@/stores/account.ts';
import { useTransactionCategoriesStore } from '@/stores/transactionCategory.ts';
import { useExchangeRatesStore } from '@/stores/exchangeRates.ts';
import { useOverviewStore } from '@/stores/overview.ts';

import { type StartEndTime, DateRange } from '@/core/datetime.ts';
import { CategoryType } from '@/core/category.ts';
import { DISPLAY_HIDDEN_AMOUNT, INCOMPLETE_AMOUNT_SUFFIX } from '@/consts/numeral.ts';

import { isNumber } from '@/lib/common.ts';
import { parseDateTimeFromUnixTime, getCurrentUnixTime } from '@/lib/datetime.ts';

interface WeeklySpendingRow {
    categoryId: string;
    categoryName: string;
    weekAmounts: number[];
    totalAmount: number;
    incomplete: boolean;
}

defineProps<{
    loading: boolean;
    disabled: boolean;
}>();

const {
    tt,
    formatDateTimeToGregorianLikeLongMonth,
    formatAmountToLocalizedNumeralsWithCurrency
} = useI18n();

const settingsStore = useSettingsStore();
const userStore = useUserStore();
const accountsStore = useAccountsStore();
const transactionCategoriesStore = useTransactionCategoriesStore();
const exchangeRatesStore = useExchangeRatesStore();
const overviewStore = useOverviewStore();

const showAmountInHomePage = computed<boolean>(() => settingsStore.appSettings.showAmountInHomePage);
const defaultCurrency = computed<string>(() => userStore.currentUserDefaultCurrency);

const weekRanges = computed<StartEndTime[]>(() => overviewStore.weeklyExpenseRanges);

const monthDisplayName = computed<string>(() => {
    if (!weekRanges.value.length) {
        return '';
    }

    return formatDateTimeToGregorianLikeLongMonth(parseDateTimeFromUnixTime(weekRanges.value[0]!.startTime));
});

const currentWeekIndex = computed<number>(() => {
    const now = getCurrentUnixTime();

    for (let i = 0; i < weekRanges.value.length; i++) {
        const week = weekRanges.value[i]!;

        if (week.startTime <= now && now <= week.endTime) {
            return i;
        }
    }

    return -1;
});

const rows = computed<WeeklySpendingRow[]>(() => {
    const weekData = overviewStore.weeklyExpenseData;

    if (!weekData || !weekData.length) {
        return [];
    }

    const rowsByCategoryId: Record<string, WeeklySpendingRow> = {};

    for (let weekIdx = 0; weekIdx < weekData.length; weekIdx++) {
        const weekResponse = weekData[weekIdx];

        if (!weekResponse || !weekResponse.items) {
            continue;
        }

        for (const item of weekResponse.items) {
            const category = transactionCategoriesStore.allTransactionCategoriesMap[item.categoryId];

            if (!category || category.type !== CategoryType.Expense) {
                continue;
            }

            const account = accountsStore.allAccountsMap[item.accountId];
            let amount: number | null = item.amount;
            let incomplete = false;

            if (account && account.currency !== defaultCurrency.value) {
                const exchangedAmount = exchangeRatesStore.getExchangedAmount(item.amount, account.currency, defaultCurrency.value);

                if (isNumber(exchangedAmount)) {
                    amount = Math.trunc(exchangedAmount);
                } else {
                    amount = null;
                    incomplete = true;
                }
            }

            let row = rowsByCategoryId[item.categoryId];

            if (!row) {
                row = {
                    categoryId: item.categoryId,
                    categoryName: category.name,
                    weekAmounts: weekData.map(() => 0),
                    totalAmount: 0,
                    incomplete: false
                };
                rowsByCategoryId[item.categoryId] = row;
            }

            if (amount !== null) {
                row.weekAmounts[weekIdx] = (row.weekAmounts[weekIdx] ?? 0) + amount;
                row.totalAmount += amount;
            }

            row.incomplete = row.incomplete || incomplete;
        }
    }

    const allRows: WeeklySpendingRow[] = [];

    for (const categoryId of Object.keys(rowsByCategoryId)) {
        allRows.push(rowsByCategoryId[categoryId]!);
    }

    allRows.sort((row1, row2) => row2.totalAmount - row1.totalAmount);

    return allRows;
});

const weekTotals = computed<number[]>(() => {
    const totals: number[] = weekRanges.value.map(() => 0);

    for (const row of rows.value) {
        for (let weekIdx = 0; weekIdx < row.weekAmounts.length; weekIdx++) {
            totals[weekIdx] = (totals[weekIdx] ?? 0) + (row.weekAmounts[weekIdx] ?? 0);
        }
    }

    return totals;
});

const grandTotal = computed<number>(() => rows.value.reduce((total, row) => total + row.totalAmount, 0));
const grandTotalIncomplete = computed<boolean>(() => rows.value.some(row => row.incomplete));

function getWeekDisplayName(week: StartEndTime): string {
    const startDay = new Date(week.startTime * 1000).getDate();
    const endDay = new Date(week.endTime * 1000).getDate();
    return `${startDay}–${endDay}`;
}

function getDisplayAmount(amount: number, incomplete?: boolean): string {
    if (!showAmountInHomePage.value) {
        return formatAmountToLocalizedNumeralsWithCurrency(DISPLAY_HIDDEN_AMOUNT, defaultCurrency.value);
    }

    return formatAmountToLocalizedNumeralsWithCurrency(amount, defaultCurrency.value) + (incomplete ? INCOMPLETE_AMOUNT_SUFFIX : '');
}

function getCellDetailsLink(categoryId: string, weekIdx: number): string {
    const week = weekRanges.value[weekIdx];

    if (!week) {
        return '/transaction/list';
    }

    return `/transaction/list?categoryIds=${categoryId}&dateType=${DateRange.Custom.type}&minTime=${week.startTime}&maxTime=${week.endTime}`;
}
</script>

<style>
.weekly-spending-table .weekly-spending-current-week {
    background-color: rgba(var(--v-theme-primary), 0.06);
}

.weekly-spending-table .weekly-spending-total-row td {
    border-top: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.weekly-spending-cell-link {
    color: inherit;
    text-decoration: none;
}

.weekly-spending-cell-link:hover {
    text-decoration: underline;
    color: rgb(var(--v-theme-primary));
}
</style>

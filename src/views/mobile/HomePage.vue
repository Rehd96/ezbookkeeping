<template>
    <f7-page ptr @ptr:refresh="reload" @page:afterin="onPageAfterIn">
        <f7-navbar>
            <f7-nav-title :title="tt('global.app.title')"></f7-nav-title>
        </f7-navbar>

        <f7-card class="home-summary-card no-margin-top" :class="{ 'skeleton-text': loading }">
            <f7-card-header class="display-block" style="padding-top: 120px;">
                <p class="no-margin">
                    <span class="card-header-content" v-if="loading">
                        <span class="home-summary-month">Month</span>
                        <span>·</span>
                        <small>Expense</small>
                    </span>
                    <span class="card-header-content" v-else-if="!loading">
                        <span class="home-summary-month">{{ displayDateRange?.thisMonth?.displayTime }}</span>
                        <span>·</span>
                        <small>{{ tt('Expense') }}</small>
                    </span>
                </p>
                <p class="no-margin">
                    <span class="month-expense" v-if="loading">0.00 USD</span>
                    <span class="month-expense" v-else-if="!loading">{{ transactionOverview && transactionOverview.thisMonth ? getDisplayExpenseAmount(transactionOverview.thisMonth) : '-' }}</span>
                    <f7-link class="display-inline-flex margin-inline-start-half" @click="showAmountInHomePage = !showAmountInHomePage">
                        <f7-icon class="ebk-hide-icon" :f7="showAmountInHomePage ? 'eye_slash_fill' : 'eye_fill'"></f7-icon>
                    </f7-link>
                </p>
                <p class="no-margin">
                    <small class="home-summary-misc" v-if="loading">Monthly income 0.00 USD</small>
                    <small class="home-summary-misc" v-else-if="!loading">
                        <span>{{ tt('Monthly income') }}</span>
                        <span>{{ transactionOverview && transactionOverview.thisMonth ? getDisplayIncomeAmount(transactionOverview.thisMonth) : '-' }}</span>
                    </small>
                </p>
            </f7-card-header>
        </f7-card>

        <template v-if="monthlyVariableBudget > 0">
            <div class="budget-cards-row">
                <f7-card class="budget-pace-card" :class="{ 'skeleton-text': loading }">
                    <f7-card-header>
                        <span class="budget-pace-title">{{ tt('Variable Spending') }}</span>
                        <f7-link :href="`/transaction/list?${overviewStore.getTransactionListPageParams({ dateType: DateRange.ThisMonth.type })}`">
                            <small>{{ tt('View Details') }}</small>
                        </f7-link>
                    </f7-card-header>
                    <f7-card-content>
                        <div class="budget-amounts">
                            <span class="budget-spent" :class="monthlySpentColorClass">{{ displayMonthlySpent }}</span>
                            <span class="budget-separator"> / </span>
                            <span class="budget-total">{{ displayMonthlyBudget }}</span>
                        </div>
                        <f7-progressbar class="budget-bar" :progress="monthlySpentPercent" :color="monthlyPaceBarColor"></f7-progressbar>
                        <div class="budget-details">
                            <div class="budget-detail-item">
                                <small class="budget-label">{{ tt('Daily Average') }}</small>
                                <span class="budget-value" :class="monthlySpentColorClass">{{ displayMonthlyDailyAvg }}</span>
                                <small class="budget-hint">{{ tt('format.misc.idealDailyAmount', { amount: displayMonthlyIdealDaily }) }}</small>
                            </div>
                            <div class="budget-detail-item">
                                <small class="budget-label">{{ tt('Remaining Budget') }}</small>
                                <span class="budget-value" :class="monthlyRemainingColorClass">{{ displayMonthlyRemaining }}</span>
                                <small class="budget-hint">{{ tt('format.misc.availablePerDayForDays', { amount: displayMonthlyRemainingDaily, count: daysLeftInThisMonth }) }}</small>
                            </div>
                        </div>
                    </f7-card-content>
                </f7-card>

                <f7-card class="budget-pace-card" :class="{ 'skeleton-text': loading }">
                    <f7-card-header>
                        <span class="budget-pace-title">{{ tt('Weekly Variable Spending') }}</span>
                        <f7-link :href="`/transaction/list?${overviewStore.getTransactionListPageParams({ dateType: DateRange.ThisWeek.type })}`">
                            <small>{{ tt('View Details') }}</small>
                        </f7-link>
                    </f7-card-header>
                    <f7-card-content>
                        <div class="budget-amounts">
                            <span class="budget-spent" :class="weeklySpentColorClass">{{ displayWeeklySpent }}</span>
                            <span class="budget-separator"> / </span>
                            <span class="budget-total">{{ displayWeeklyBudget }}</span>
                        </div>
                        <f7-progressbar class="budget-bar" :progress="weeklySpentPercent" :color="weeklyPaceBarColor"></f7-progressbar>
                        <div class="budget-details">
                            <div class="budget-detail-item">
                                <small class="budget-label">{{ tt('Daily Average') }}</small>
                                <span class="budget-value" :class="weeklySpentColorClass">{{ displayWeeklyDailyAvg }}</span>
                                <small class="budget-hint">{{ tt('format.misc.idealDailyAmount', { amount: displayWeeklyIdealDaily }) }}</small>
                            </div>
                            <div class="budget-detail-item">
                                <small class="budget-label">{{ tt('Remaining Budget') }}</small>
                                <span class="budget-value" :class="weeklyRemainingColorClass">{{ displayWeeklyRemaining }}</span>
                                <small class="budget-hint">{{ tt('format.misc.availablePerDayForDays', { amount: displayWeeklyRemainingDaily, count: daysLeftInThisWeek }) }}</small>
                            </div>
                        </div>
                    </f7-card-content>
                </f7-card>
            </div>
        </template>

        <f7-list strong inset dividers class="margin-top overview-transaction-list" :class="{ 'skeleton-text': loading }">
            <f7-list-item :link="`/transaction/list?${overviewStore.getTransactionListPageParams({ dateType: DateRange.Today.type })}`" chevron-center>
                <template #media>
                    <f7-icon f7="calendar_today"></f7-icon>
                </template>
                <template #title>
                    <div class="padding-top-half">
                        <span v-if="loading">Today</span>
                        <span v-else-if="!loading">{{ tt('Today') }}</span>
                    </div>
                </template>
                <template #footer>
                    <div class="overview-transaction-footer padding-bottom-half">
                        <span v-if="loading">MM/DD/YYYY</span>
                        <span v-else-if="!loading">{{ displayDateRange?.today?.displayTime }}</span>
                    </div>
                </template>
                <template #after>
                    <div class="overview-transaction-amount">
                        <div class="text-income text-align-right">
                            <small v-if="loading">0.00 USD</small>
                            <small v-else-if="!loading && transactionOverview.today && transactionOverview.today.valid">{{ getDisplayIncomeAmount(transactionOverview.today) }}</small>
                        </div>
                        <div class="text-expense text-align-right">
                            <small v-if="loading">0.00 USD</small>
                            <small v-else-if="!loading && transactionOverview.today && transactionOverview.today.valid">{{ getDisplayExpenseAmount(transactionOverview.today) }}</small>
                        </div>
                    </div>
                </template>
            </f7-list-item>

            <f7-list-item :link="`/transaction/list?${overviewStore.getTransactionListPageParams({ dateType: DateRange.ThisWeek.type })}`" chevron-center>
                <template #media>
                    <f7-icon f7="calendar"></f7-icon>
                </template>
                <template #title>
                    <div class="padding-top-half">
                        <span v-if="loading">This Week</span>
                        <span v-else-if="!loading">{{ tt('This Week') }}</span>
                    </div>
                </template>
                <template #footer>
                    <div class="overview-transaction-footer padding-bottom-half">
                        <span v-if="loading">MM/DD</span>
                        <span v-else-if="!loading">{{ displayDateRange?.thisWeek?.startTime }}</span>
                        <span>-</span>
                        <span v-if="loading">MM/DD</span>
                        <span v-else-if="!loading">{{ displayDateRange?.thisWeek?.endTime }}</span>
                    </div>
                </template>
                <template #after>
                    <div class="overview-transaction-amount">
                        <div class="text-income text-align-right">
                            <small v-if="loading">0.00 USD</small>
                            <small v-else-if="!loading && transactionOverview.thisWeek && transactionOverview.thisWeek.valid">{{ getDisplayIncomeAmount(transactionOverview.thisWeek) }}</small>
                        </div>
                        <div class="text-expense text-align-right">
                            <small v-if="loading">0.00 USD</small>
                            <small v-else-if="!loading && transactionOverview.thisWeek && transactionOverview.thisWeek.valid">{{ getDisplayExpenseAmount(transactionOverview.thisWeek) }}</small>
                        </div>
                    </div>
                </template>
            </f7-list-item>

            <f7-list-item :link="`/transaction/list?${overviewStore.getTransactionListPageParams({ dateType: DateRange.ThisMonth.type })}`" chevron-center>
                <template #media>
                    <f7-icon f7="calendar"></f7-icon>
                </template>
                <template #title>
                    <div class="padding-top-half">
                        <span v-if="loading">This Month</span>
                        <span v-else-if="!loading">{{ tt('This Month') }}</span>
                    </div>
                </template>
                <template #footer>
                    <div class="overview-transaction-footer padding-bottom-half">
                        <span v-if="loading">MM/DD</span>
                        <span v-else-if="!loading">{{ displayDateRange?.thisMonth?.startTime }}</span>
                        <span>-</span>
                        <span v-if="loading">MM/DD</span>
                        <span v-else-if="!loading">{{ displayDateRange?.thisMonth?.endTime }}</span>
                    </div>
                </template>
                <template #after>
                    <div class="overview-transaction-amount">
                        <div class="text-income text-align-right">
                            <small v-if="loading">0.00 USD</small>
                            <small v-else-if="!loading && transactionOverview.thisMonth && transactionOverview.thisMonth.valid">{{ getDisplayIncomeAmount(transactionOverview.thisMonth) }}</small>
                        </div>
                        <div class="text-expense text-align-right">
                            <small v-if="loading">0.00 USD</small>
                            <small v-else-if="!loading && transactionOverview.thisMonth && transactionOverview.thisMonth.valid">{{ getDisplayExpenseAmount(transactionOverview.thisMonth) }}</small>
                        </div>
                    </div>
                </template>
            </f7-list-item>

            <f7-list-item :link="`/transaction/list?${overviewStore.getTransactionListPageParams({ dateType: DateRange.ThisYear.type })}`" chevron-center>
                <template #media>
                    <f7-icon f7="square_stack_3d_up"></f7-icon>
                </template>
                <template #title>
                    <div class="padding-top-half">
                        <span v-if="loading">This Year</span>
                        <span v-else-if="!loading">{{ tt('This Year') }}</span>
                    </div>
                </template>
                <template #footer>
                    <div class="overview-transaction-footer padding-bottom-half">
                        <span v-if="loading">YYYY</span>
                        <span v-else-if="!loading">{{ displayDateRange?.thisYear?.displayTime }}</span>
                    </div>
                </template>
                <template #after>
                    <div class="overview-transaction-amount">
                        <div class="text-income text-align-right">
                            <small v-if="loading">0.00 USD</small>
                            <small v-else-if="!loading && transactionOverview.thisYear && transactionOverview.thisYear.valid">{{ getDisplayIncomeAmount(transactionOverview.thisYear) }}</small>
                        </div>
                        <div class="text-expense text-align-right">
                            <small v-if="loading">0.00 USD</small>
                            <small v-else-if="!loading && transactionOverview.thisYear && transactionOverview.thisYear.valid">{{ getDisplayExpenseAmount(transactionOverview.thisYear) }}</small>
                        </div>
                    </div>
                </template>
            </f7-list-item>
        </f7-list>

        <f7-block-title v-if="weeklySpendingRows.length || loading">{{ tt('Weekly Spending Breakdown') }}</f7-block-title>
        <f7-list strong inset dividers class="weekly-spending-list" :class="{ 'skeleton-text': loading }" v-if="weeklySpendingRows.length || loading">
            <f7-list-item v-if="loading" v-for="n in 4" :key="n" title="Loading..." after="..."></f7-list-item>
            <f7-list-item
                v-else
                v-for="row in weeklySpendingRows"
                :key="row.categoryId"
                :link="`/transaction/list?categoryIds=${row.categoryId}&dateType=${DateRange.ThisWeek.type}`"
                :title="row.categoryName"
                :after="getDisplayWeeklyAmount(row.weekAmount, row.incomplete)"
            ></f7-list-item>
            <f7-list-item v-if="!loading && weeklySpendingRows.length" :title="tt('Total')" :after="getDisplayWeeklyAmount(weeklySpendingTotal)"></f7-list-item>
        </f7-list>

        <f7-toolbar tabbar icons bottom class="main-tabbar">
            <f7-link class="link" href="/transaction/list">
                <f7-icon f7="square_list"></f7-icon>
                <span class="tabbar-label">{{ tt('Details') }}</span>
            </f7-link>
            <f7-link class="link" href="/account/list">
                <f7-icon f7="creditcard"></f7-icon>
                <span class="tabbar-label">{{ tt('Accounts') }}</span>
            </f7-link>
            <f7-link id="homepage-add-button" class="link dragenabled"
                     href="/transaction/add" @taphold="openTransactionTemplatePopover">
                <f7-icon f7="plus_square" class="ebk-tarbar-big-icon"></f7-icon>
            </f7-link>
            <f7-link class="link" href="/statistic/transaction">
                <f7-icon f7="chart_pie"></f7-icon>
                <span class="tabbar-label">{{ tt('Statistics') }}</span>
            </f7-link>
            <f7-link class="link" href="/settings">
                <f7-icon f7="gear_alt"></f7-icon>
                <span class="tabbar-label">{{ tt('Settings') }}</span>
            </f7-link>
        </f7-toolbar>

        <f7-popover class="template-popover-menu" target-el="#homepage-add-button"
                    v-model:opened="showTransactionTemplatePopover">
            <f7-list dividers v-if="allTransactionTemplates">
                <f7-list-item key="AIImageRecognition" :title="tt('AI Image Recognition')"
                              @click="showAIReceiptImageRecognitionSheet = true; showTransactionTemplatePopover = false"
                              v-if="isTransactionFromAIImageRecognitionEnabled()">
                    <template #media>
                        <f7-icon f7="wand_stars"></f7-icon>
                    </template>
                </f7-list-item>
                <f7-list-item :key="template.id" :title="template.name"
                              :link="'/transaction/add?templateId=' + template.id"
                              v-for="template in allTransactionTemplates">
                    <template #media>
                        <f7-icon f7="doc_plaintext"></f7-icon>
                    </template>
                </f7-list-item>
            </f7-list>
        </f7-popover>

        <a-i-image-recognition-sheet ref="aiImageRecognitionSheet"
                                     v-model:show="showAIReceiptImageRecognitionSheet"
                                     @recognition:change="onReceiptRecognitionChanged"/>
    </f7-page>
</template>

<script setup lang="ts">
import AIImageRecognitionSheet from '@/components/mobile/AIImageRecognitionSheet.vue';

import { ref, computed, useTemplateRef } from 'vue';
import type { Router } from 'framework7/types';

import { useI18n } from '@/locales/helpers.ts';
import { useI18nUIComponents } from '@/lib/ui/mobile.ts';
import { useHomePageBase } from '@/views/base/HomePageBase.ts';

import { useSettingsStore } from '@/stores/setting.ts';
import { useUserStore } from '@/stores/user.ts';
import { useAccountsStore } from '@/stores/account.ts';
import { useTransactionCategoriesStore } from '@/stores/transactionCategory.ts';
import { useTransactionTemplatesStore } from '@/stores/transactionTemplate.ts';
import { useExchangeRatesStore } from '@/stores/exchangeRates.ts';
import { useOverviewStore } from '@/stores/overview.ts';

import { DateRange } from '@/core/datetime.ts';
import { CategoryType } from '@/core/category.ts';
import { TemplateType } from '@/core/template.ts';
import { TransactionTemplate } from '@/models/transaction_template.ts';
import type { RecognizedReceiptImageResponse } from '@/models/large_language_model.ts';
import { DISPLAY_HIDDEN_AMOUNT, INCOMPLETE_AMOUNT_SUFFIX } from '@/consts/numeral.ts';

import { isNumber } from '@/lib/common.ts';

import { isUserLogined, isUserUnlocked } from '@/lib/userstate.ts';
import { getShareCacheImageBlob } from '@/lib/cache.ts';
import { isTransactionFromAIImageRecognitionEnabled } from '@/lib/server_settings.ts';

type AIImageRecognitionSheetType = InstanceType<typeof AIImageRecognitionSheet>;

const props = defineProps<{
    f7router: Router.Router;
}>();

const { tt, formatAmountToLocalizedNumeralsWithCurrency } = useI18n();
const { showToast } = useI18nUIComponents();

const {
    showAmountInHomePage,
    displayDateRange,
    transactionOverview,
    getDisplayIncomeAmount,
    getDisplayExpenseAmount
} = useHomePageBase();

const settingsStore = useSettingsStore();
const userStore = useUserStore();
const accountsStore = useAccountsStore();
const transactionCategoriesStore = useTransactionCategoriesStore();
const transactionTemplatesStore = useTransactionTemplatesStore();
const exchangeRatesStore = useExchangeRatesStore();
const overviewStore = useOverviewStore();

// ── Budget helpers ─────────────────────────────────────────────────────────

const defaultCurrency = computed<string>(() => userStore.currentUserDefaultCurrency);
const monthlyVariableBudget = computed<number>(() => settingsStore.appSettings.monthlyVariableBudgetInHomePage);

function fmt(amount: number, incomplete?: boolean): string {
    if (!showAmountInHomePage.value) {
        return formatAmountToLocalizedNumeralsWithCurrency(DISPLAY_HIDDEN_AMOUNT, defaultCurrency.value);
    }
    return formatAmountToLocalizedNumeralsWithCurrency(amount, defaultCurrency.value) + (incomplete ? INCOMPLETE_AMOUNT_SUFFIX : '');
}

// Monthly budget
const monthlySpentAmount = computed<number>(() => overviewStore.variableExpenseThisMonth.expenseAmount);
const monthlySpentIncomplete = computed<boolean>(() => overviewStore.variableExpenseThisMonth.incompleteExpenseAmount);

const daysInThisMonth = computed<number>(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
});
const dayOfMonth = computed<number>(() => new Date().getDate());
const daysLeftInThisMonth = computed<number>(() => daysInThisMonth.value - dayOfMonth.value + 1);

const monthlyIdealSpentToDate = computed<number>(() =>
    Math.round(monthlyVariableBudget.value * dayOfMonth.value / daysInThisMonth.value)
);
const monthlyIdealDaily = computed<number>(() => Math.round(monthlyVariableBudget.value / daysInThisMonth.value));
const monthlyActualDaily = computed<number>(() => Math.round(monthlySpentAmount.value / dayOfMonth.value));
const monthlyRemaining = computed<number>(() => monthlyVariableBudget.value - monthlySpentAmount.value);
const monthlyRemainingDaily = computed<number>(() =>
    monthlyRemaining.value > 0 ? Math.round(monthlyRemaining.value / daysLeftInThisMonth.value) : 0
);
const monthlySpentPercent = computed<number>(() => {
    if (monthlyVariableBudget.value <= 0) return 0;
    return Math.min(100, monthlySpentAmount.value / monthlyVariableBudget.value * 100);
});
const monthlyPaceBarColor = computed<string>(() => {
    if (monthlySpentAmount.value > monthlyVariableBudget.value) return 'red';
    if (monthlySpentAmount.value > monthlyIdealSpentToDate.value) return 'orange';
    return 'green';
});
const monthlySpentColorClass = computed<string>(() => {
    if (monthlySpentAmount.value > monthlyVariableBudget.value) return 'text-color-red';
    if (monthlySpentAmount.value > monthlyIdealSpentToDate.value) return 'text-color-orange';
    return 'text-color-green';
});
const monthlyRemainingColorClass = computed<string>(() => monthlyRemaining.value < 0 ? 'text-color-red' : '');

const displayMonthlySpent = computed<string>(() => fmt(monthlySpentAmount.value, monthlySpentIncomplete.value));
const displayMonthlyBudget = computed<string>(() => fmt(monthlyVariableBudget.value));
const displayMonthlyDailyAvg = computed<string>(() => fmt(monthlyActualDaily.value));
const displayMonthlyIdealDaily = computed<string>(() => fmt(monthlyIdealDaily.value));
const displayMonthlyRemaining = computed<string>(() => fmt(monthlyRemaining.value));
const displayMonthlyRemainingDaily = computed<string>(() => fmt(monthlyRemainingDaily.value));

// Weekly budget
const weeklySpentAmount = computed<number>(() => overviewStore.variableExpenseThisWeek.expenseAmount);
const weeklySpentIncomplete = computed<boolean>(() => overviewStore.variableExpenseThisWeek.incompleteExpenseAmount);

const daysInThisWeek = computed<number>(() => {
    const range = overviewStore.transactionDataRange.thisWeek;
    return Math.round((range.endTime - range.startTime + 1) / 86400);
});
const dayOfCurrentWeekElapsed = computed<number>(() => {
    const range = overviewStore.transactionDataRange.thisWeek;
    const now = Math.floor(Date.now() / 1000);
    return Math.min(daysInThisWeek.value, Math.floor((now - range.startTime) / 86400) + 1);
});
const daysLeftInThisWeek = computed<number>(() => daysInThisWeek.value - dayOfCurrentWeekElapsed.value + 1);

const weeklyBudget = computed<number>(() =>
    Math.round(monthlyVariableBudget.value * daysInThisWeek.value / daysInThisMonth.value)
);
const weeklyIdealSpentToDate = computed<number>(() =>
    Math.round(weeklyBudget.value * dayOfCurrentWeekElapsed.value / daysInThisWeek.value)
);
const weeklyIdealDaily = computed<number>(() => Math.round(weeklyBudget.value / daysInThisWeek.value));
const weeklyActualDaily = computed<number>(() =>
    dayOfCurrentWeekElapsed.value > 0 ? Math.round(weeklySpentAmount.value / dayOfCurrentWeekElapsed.value) : 0
);
const weeklyRemaining = computed<number>(() => weeklyBudget.value - weeklySpentAmount.value);
const weeklyRemainingDaily = computed<number>(() =>
    weeklyRemaining.value > 0 ? Math.round(weeklyRemaining.value / daysLeftInThisWeek.value) : 0
);
const weeklySpentPercent = computed<number>(() => {
    if (weeklyBudget.value <= 0) return 0;
    return Math.min(100, weeklySpentAmount.value / weeklyBudget.value * 100);
});
const weeklyPaceBarColor = computed<string>(() => {
    if (weeklySpentAmount.value > weeklyBudget.value) return 'red';
    if (weeklySpentAmount.value > weeklyIdealSpentToDate.value) return 'orange';
    return 'green';
});
const weeklySpentColorClass = computed<string>(() => {
    if (weeklySpentAmount.value > weeklyBudget.value) return 'text-color-red';
    if (weeklySpentAmount.value > weeklyIdealSpentToDate.value) return 'text-color-orange';
    return 'text-color-green';
});
const weeklyRemainingColorClass = computed<string>(() => weeklyRemaining.value < 0 ? 'text-color-red' : '');

const displayWeeklySpent = computed<string>(() => fmt(weeklySpentAmount.value, weeklySpentIncomplete.value));
const displayWeeklyBudget = computed<string>(() => fmt(weeklyBudget.value));
const displayWeeklyDailyAvg = computed<string>(() => fmt(weeklyActualDaily.value));
const displayWeeklyIdealDaily = computed<string>(() => fmt(weeklyIdealDaily.value));
const displayWeeklyRemaining = computed<string>(() => fmt(weeklyRemaining.value));
const displayWeeklyRemainingDaily = computed<string>(() => fmt(weeklyRemainingDaily.value));

// Weekly spending breakdown (current week, all categories)
interface MobileWeeklyRow {
    categoryId: string;
    categoryName: string;
    weekAmount: number;
    incomplete: boolean;
}

const currentWeekIndex = computed<number>(() => {
    const ranges = overviewStore.weeklyExpenseRanges;
    const now = Math.floor(Date.now() / 1000);
    for (let i = 0; i < ranges.length; i++) {
        const w = ranges[i]!;
        if (w.startTime <= now && now <= w.endTime) return i;
    }
    return -1;
});

const weeklySpendingRows = computed<MobileWeeklyRow[]>(() => {
    const weekData = overviewStore.weeklyExpenseData;
    const weekIdx = currentWeekIndex.value;

    if (!weekData || weekIdx < 0 || !weekData[weekIdx]?.items) return [];

    const rowMap: Record<string, MobileWeeklyRow> = {};

    for (const item of weekData[weekIdx]!.items) {
        const category = transactionCategoriesStore.allTransactionCategoriesMap[item.categoryId];
        if (!category || category.type !== CategoryType.Expense) continue;

        const account = accountsStore.allAccountsMap[item.accountId];
        let amount: number | null = item.amount;
        let incomplete = false;

        if (account && account.currency !== defaultCurrency.value) {
            const ex = exchangeRatesStore.getExchangedAmount(item.amount, account.currency, defaultCurrency.value);
            if (isNumber(ex)) {
                amount = Math.trunc(ex);
            } else {
                amount = null;
                incomplete = true;
            }
        }

        let row = rowMap[item.categoryId];
        if (!row) {
            row = { categoryId: item.categoryId, categoryName: category.name, weekAmount: 0, incomplete: false };
            rowMap[item.categoryId] = row;
        }
        if (amount !== null) row.weekAmount += amount;
        row.incomplete = row.incomplete || incomplete;
    }

    return Object.values(rowMap).sort((a, b) => b.weekAmount - a.weekAmount);
});

const weeklySpendingTotal = computed<number>(() => weeklySpendingRows.value.reduce((s, r) => s + r.weekAmount, 0));

function getDisplayWeeklyAmount(amount: number, incomplete?: boolean): string {
    return fmt(amount, incomplete);
}

const aiImageRecognitionSheet = useTemplateRef<AIImageRecognitionSheetType>('aiImageRecognitionSheet');

const loading = ref<boolean>(true);
const showTransactionTemplatePopover = ref<boolean>(false);
const showAIReceiptImageRecognitionSheet = ref<boolean>(false);

const allTransactionTemplates = computed<TransactionTemplate[]>(() => {
    const allTemplates = transactionTemplatesStore.allVisibleTemplates;
    return allTemplates[TemplateType.Normal.type] || [];
});

function openTransactionTemplatePopover(): void {
    if (isTransactionFromAIImageRecognitionEnabled() || (allTransactionTemplates.value && allTransactionTemplates.value.length)) {
        showTransactionTemplatePopover.value = true;
    }
}

function init(): void {
    if (isUserLogined() && isUserUnlocked()) {
        loading.value = true;

        const promises = [
            getShareCacheImageBlob(),
            accountsStore.loadAllAccounts({ force: false }),
            transactionCategoriesStore.loadAllCategories({ force: false }),
            transactionTemplatesStore.loadAllTemplates({ templateType: TemplateType.Normal.type,  force: false }),
            overviewStore.loadTransactionOverview({ force: false }),
            overviewStore.loadWeeklyExpenseStatistics({ force: false })
        ];

        if (monthlyVariableBudget.value > 0) {
            promises.push(overviewStore.loadVariableExpenseThisMonth({ force: false }) as never);
            promises.push(overviewStore.loadVariableExpenseThisWeek({ force: false }) as never);
        }

        Promise.all(promises).then(responses => {
            if (responses[0] && responses[0] instanceof Blob) {
                aiImageRecognitionSheet.value?.loadImage(responses[0]);
                showAIReceiptImageRecognitionSheet.value = true;
            }

            loading.value = false;
        }).catch(error => {
            loading.value = false;

            if (!error.processed) {
                showToast(error.message || error);
            }
        });
    }
}

function reload(done?: () => void): void {
    const force = !!done;

    const reloadPromises: Promise<unknown>[] = [
        overviewStore.loadTransactionOverview({ force: force }),
        overviewStore.loadWeeklyExpenseStatistics({ force: force })
    ];

    if (monthlyVariableBudget.value > 0) {
        reloadPromises.push(overviewStore.loadVariableExpenseThisMonth({ force: force }));
        reloadPromises.push(overviewStore.loadVariableExpenseThisWeek({ force: force }));
    }

    Promise.all(reloadPromises).then(() => {
        done?.();

        if (force) {
            showToast('Data has been updated');
        }
    }).catch(error => {
        done?.();

        if (!error.processed) {
            showToast(error.message || error);
        }
    });
}

function onReceiptRecognitionChanged(result: RecognizedReceiptImageResponse): void {
    const params: string[] = [];

    if (result.type) {
        params.push(`type=${result.type}`);
    }

    if (result.time) {
        params.push(`time=${result.time}`);
    }

    if (result.categoryId) {
        params.push(`categoryId=${result.categoryId}`);
    }

    if (result.sourceAccountId) {
        params.push(`accountId=${result.sourceAccountId}`);
    }

    if (result.destinationAccountId) {
        params.push(`destinationAccountId=${result.destinationAccountId}`);
    }

    if (result.sourceAmount) {
        params.push(`amount=${result.sourceAmount}`);
    }

    if (result.destinationAmount) {
        params.push(`destinationAmount=${result.destinationAmount}`);
    }

    if (result.tagIds) {
        params.push(`tagIds=${result.tagIds.join(',')}`);
    }

    if (result.comment) {
        params.push(`comment=${encodeURIComponent(result.comment)}`);
    }

    params.push(`noTransactionDraft=true`);

    props.f7router.navigate(`/transaction/add?${params.join('&')}`);
}

function onPageAfterIn(): void {
    if (!loading.value) {
        reload();
    }
}

init();
</script>

<style>
.budget-cards-row {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.budget-pace-card {
    margin-top: 8px;
}

.budget-pace-card .f7-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 4px;
}

.budget-pace-title {
    font-weight: 600;
    font-size: 0.9em;
}

.budget-amounts {
    display: flex;
    align-items: baseline;
    margin-bottom: 6px;
}

.budget-spent {
    font-size: 1.4em;
    font-weight: 600;
}

.budget-separator {
    margin: 0 4px;
    color: var(--f7-list-item-subtitle-text-color);
}

.budget-total {
    font-size: 0.95em;
    color: var(--f7-list-item-subtitle-text-color);
}

.budget-bar {
    margin-bottom: 10px;
}

.budget-details {
    display: flex;
    gap: 16px;
}

.budget-detail-item {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.budget-label {
    color: var(--f7-list-item-subtitle-text-color);
    font-size: 0.75em;
}

.budget-value {
    font-size: 0.95em;
    font-weight: 500;
}

.budget-hint {
    color: var(--f7-list-item-subtitle-text-color);
    font-size: 0.75em;
}

.home-summary-card {
    background-color: var(--f7-color-yellow);
}

.home-summary-card .home-summary-month {
    font-size: 1.3em;
}

.home-summary-card .month-expense {
    font-size: 1.5em;
}

.home-summary-card .home-summary-misc {
    opacity: 0.6;
}

.home-summary-misc > span {
    margin-inline-end: 4px;
}

.home-summary-misc > span:last-child {
    margin-inline-end: 0;
}

.dark .home-summary-card {
    background-color: var(--f7-theme-color);
}

.dark .home-summary-card a {
    color: var(--f7-text-color);
    opacity: 0.6;
}

.overview-transaction-list .item-title > div {
    overflow: hidden;
    text-overflow: ellipsis;
}

.overview-transaction-list .item-after {
    max-width: 100%;
}

.overview-transaction-list .overview-transaction-footer {
    padding-top: 6px;
    font-size: var(--ebk-large-footer-font-size);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.overview-transaction-list .overview-transaction-footer > span {
    margin-inline-end: 4px;
}

.overview-transaction-list .overview-transaction-amount {
    max-width: 100%;
}

.overview-transaction-list .overview-transaction-amount > div {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
}

.tabbar.main-tabbar .link i + span.tabbar-label {
    margin-top: var(--ebk-icon-text-margin);
}

.tabbar.main-tabbar .link i.ebk-tarbar-big-icon {
    font-size: var(--ebk-big-icon-button-size);
    width: var(--ebk-big-icon-button-size);
    height: var(--ebk-big-icon-button-size);
    line-height: var(--ebk-big-icon-button-size);
}

.template-popover-menu .popover-inner {
    max-height: 400px;
    overflow-y: auto;
}
</style>

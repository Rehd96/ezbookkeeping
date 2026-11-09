<template>
    <v-card :class="{ 'disabled': disabled }">
        <v-card-item>
            <div class="d-flex align-center flex-wrap">
                <v-avatar color="primary" variant="tonal" size="38" class="me-3">
                    <v-icon size="24" :icon="mdiCashCheck" />
                </v-avatar>
                <div>
                    <v-card-title class="pa-0 text-h6 font-weight-bold">
                        {{ tt('Cash Flow & Upcoming Obligations') }}
                    </v-card-title>
                    <v-card-subtitle class="pa-0 text-caption">
                        {{ tt('Real available cash, pending direct debits, and 30-day runway') }}
                    </v-card-subtitle>
                </div>
                <v-spacer />
                <v-chip
                    v-if="intesaShortfall > 0"
                    color="error"
                    variant="flat"
                    size="small"
                    class="font-weight-bold my-1"
                    :prepend-icon="mdiAlertCircleOutline"
                >
                    {{ tt('Intesa Shortfall') }}: {{ formatCurrency(intesaShortfall) }}
                </v-chip>
                <v-chip
                    v-else
                    color="success"
                    variant="tonal"
                    size="small"
                    class="font-weight-medium my-1"
                    :prepend-icon="mdiCheckCircleOutline"
                >
                    {{ tt('Direct Debits Covered') }}
                </v-chip>
            </div>
        </v-card-item>

        <v-card-text class="pt-0">
            <!-- Key Liquidity Metrics Row -->
            <v-row class="mb-2">
                <v-col cols="12" sm="6" md="3">
                    <v-card variant="outlined" class="pa-3 rounded-lg h-100">
                        <span class="text-caption text-medium-emphasis d-block">{{ tt('Liquid Bank Balance') }}</span>
                        <span class="text-h6 font-weight-bold">{{ displayLiquidCash }}</span>
                        <div class="text-caption text-disabled mt-1">
                            {{ tt('Protected Lifetime Savings') }}
                        </div>
                    </v-card>
                </v-col>

                <v-col cols="12" sm="6" md="3">
                    <v-card variant="outlined" class="pa-3 rounded-lg h-100 border-warning">
                        <span class="text-caption text-medium-emphasis d-block">{{ tt('Pending Fixed Bills') }}</span>
                        <span class="text-h6 font-weight-bold text-warning">{{ displayPendingFixed }}</span>
                        <div class="text-caption text-disabled mt-1">
                            {{ pendingBills.length }} {{ tt('bills due before next paycheck') }}
                        </div>
                    </v-card>
                </v-col>

                <v-col cols="12" sm="6" md="3">
                    <v-card
                        variant="tonal"
                        :color="remainingPaycheckVariableBudget >= 0 ? 'primary' : 'error'"
                        class="pa-3 rounded-lg h-100"
                    >
                        <span class="text-caption font-weight-bold text-uppercase d-block">{{ tt('Paycheck Variable Budget Left') }}</span>
                        <span class="text-h6 font-weight-bold" :class="remainingPaycheckVariableBudget >= 0 ? '' : 'text-error'">
                            {{ displayRemainingPaycheckBudget }}
                        </span>
                        <div class="text-caption mt-1 font-weight-medium">
                            <span v-if="remainingPaycheckVariableBudget > 0">
                                {{ formatCurrency(dynamicDailyAllowance) }}/{{ tt('day') }} ({{ daysLeftInCycle }} {{ tt('days left') }})
                            </span>
                            <span v-else class="text-error font-weight-bold">
                                {{ tt('Budget Exceeded') }} · 0 {{ tt('EUR') }}/{{ tt('day') }}
                            </span>
                        </div>
                    </v-card>
                </v-col>

                <v-col cols="12" sm="6" md="3">
                    <v-card
                        variant="outlined"
                        class="pa-3 rounded-lg h-100"
                        :class="intesaShortfall > 0 ? 'border-error bg-error-lighten-5' : 'border-success'"
                    >
                        <div class="d-flex justify-space-between align-center">
                            <span class="text-caption text-medium-emphasis">{{ tt('Intesa Account Buffer') }}</span>
                            <span class="text-caption font-weight-bold" :class="intesaShortfall > 0 ? 'text-error' : 'text-success'">
                                {{ intesaShortfall > 0 ? tt('Action Needed') : tt('OK') }}
                            </span>
                        </div>
                        <span class="text-h6 font-weight-bold" :class="intesaShortfall > 0 ? 'text-error' : 'text-success'">
                            {{ displayIntesaBalance }}
                        </span>
                        <div class="text-caption mt-1" :class="intesaShortfall > 0 ? 'text-error' : 'text-medium-emphasis'">
                            <span v-if="intesaShortfall > 0">
                                {{ tt('Needs +') }} {{ formatCurrency(intesaShortfall + 3000) }} {{ tt('from TR before') }} {{ intesaNextBillDateText }}
                            </span>
                            <span v-else>
                                {{ formatCurrency(intesaPendingTotal) }} {{ tt('upcoming debits') }}
                            </span>
                        </div>
                    </v-card>
                </v-col>
            </v-row>

            <!-- Navigation Tabs -->
            <v-tabs v-model="activeTab" density="comfortable" color="primary" class="border-b mb-3">
                <v-tab value="pacing">
                    <v-icon size="18" start :icon="mdiChartAreaspline" />
                    {{ tt('Daily Pacing (Ideale vs. Pivot)') }}
                </v-tab>
                <v-tab value="timeline">
                    <v-icon size="18" start :icon="mdiCalendarClockOutline" />
                    {{ tt('Upcoming Bills') }} ({{ pendingBills.length }})
                </v-tab>
                <v-tab value="runway">
                    <v-icon size="18" start :icon="mdiChartTimelineVariant" />
                    {{ tt('30-Day Cash Flow Runway') }}
                </v-tab>
                <v-tab value="whatif">
                    <v-icon size="18" start :icon="mdiCalculatorVariantOutline" />
                    {{ tt('What-If Simulator') }}
                </v-tab>
            </v-tabs>

            <v-window v-model="activeTab">
                <!-- Tab 1: Daily Pacing (Excel Rows 67, 68, 69) -->
                <v-window-item value="pacing">
                    <v-row class="mb-2">
                        <v-col cols="12" sm="4">
                            <v-card variant="tonal" :color="pacingDifference >= 0 ? 'success' : 'error'" class="pa-3 rounded-lg h-100">
                                <span class="text-caption font-weight-medium d-block">
                                    {{ tt('Pacing Status (DIFFerenza)') }}
                                </span>
                                <span class="text-h6 font-weight-bold">
                                    {{ pacingDifference >= 0 ? '+' : '' }}{{ formatCurrency(pacingDifference) }}
                                </span>
                                <div class="text-caption mt-1">
                                    <span v-if="pacingDifference >= 0">
                                        {{ tt('Under Budget (Cushion accumulated)') }}
                                    </span>
                                    <span v-else>
                                        {{ tt('Over Budget (Pacing too fast)') }}
                                    </span>
                                </div>
                            </v-card>
                        </v-col>

                        <v-col cols="12" sm="4">
                            <v-card variant="outlined" class="pa-3 rounded-lg h-100">
                                <span class="text-caption text-medium-emphasis d-block">
                                    {{ tt('Dynamic Daily Allowance') }}
                                </span>
                                <div class="d-flex align-baseline">
                                    <span class="text-h6 font-weight-bold">{{ formatCurrency(dynamicDailyAllowance) }}</span>
                                    <span class="text-caption text-disabled ms-1">/ {{ tt('day') }}</span>
                                </div>
                                <div class="text-caption text-disabled mt-1">
                                    {{ daysLeftInCycle }} {{ tt('days left until next paycheck') }}
                                </div>
                            </v-card>
                        </v-col>

                        <v-col cols="12" sm="4">
                            <v-card variant="outlined" class="pa-3 rounded-lg h-100">
                                <span class="text-caption text-medium-emphasis d-block">
                                    {{ tt('Paycheck Cycle Progress') }}
                                </span>
                                <span class="text-h6 font-weight-bold">
                                    {{ tt('Day') }} {{ currentCycleDay }} / {{ totalDaysInCycle }}
                                </span>
                                <div class="text-caption mt-1" :class="velocityVsPriorMonth >= 0 ? 'text-success' : 'text-warning'">
                                    <span>
                                        {{ velocityVsPriorMonth >= 0 ? '▼ ' : '▲ ' }}{{ formatCurrency(Math.abs(velocityVsPriorMonth)) }} {{ tt('vs. prior month pace') }}
                                    </span>
                                </div>
                            </v-card>
                        </v-col>
                    </v-row>

                    <!-- Pacing 3-Lines ECharts Graph -->
                    <div style="height: 300px;" class="w-100 mt-2">
                        <v-chart autoresize :option="pacingChartOptions" class="w-100 h-100" />
                    </div>

                    <!-- Pacing Legend & Explanation -->
                    <div class="d-flex justify-center flex-wrap gap-4 mt-3 text-caption text-medium-emphasis">
                        <span class="me-4 d-flex align-center">
                            <span class="legend-dot bg-info me-1"></span>
                            {{ tt('Spese Ideali (Row 67 linear allowance)') }}
                        </span>
                        <span class="me-4 d-flex align-center">
                            <span class="legend-dot bg-warning me-1"></span>
                            {{ tt('Spese Pivot (Row 68 actual cumulative spend)') }}
                        </span>
                        <span class="d-flex align-center">
                            <span class="legend-dot bg-grey me-1"></span>
                            {{ tt('Mese Precedente (Row 35 benchmark ghost line)') }}
                        </span>
                    </div>
                </v-window-item>

                <!-- Tab 2: Upcoming Bills Timeline -->
                <v-window-item value="timeline">
                    <div v-if="!pendingBills.length" class="text-center py-6 text-disabled">
                        {{ tt('No pending fixed bills remaining for this month!') }}
                    </div>
                    <v-table density="compact" v-else class="text-no-wrap">
                        <thead>
                            <tr>
                                <th>{{ tt('Due Date') }}</th>
                                <th>{{ tt('Expense / Bill') }}</th>
                                <th>{{ tt('Account') }}</th>
                                <th class="text-end">{{ tt('Amount') }}</th>
                                <th class="text-center">{{ tt('Status') }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="bill in pendingBills" :key="bill.name + bill.day">
                                <td>
                                    <div class="d-flex align-center">
                                        <v-chip
                                            size="x-small"
                                            :color="bill.daysUntil <= 1 ? 'error' : (bill.daysUntil <= 7 ? 'warning' : 'default')"
                                            class="font-weight-bold me-2"
                                        >
                                            {{ getDaysUntilText(bill.daysUntil) }}
                                        </v-chip>
                                        <span class="text-body-2 font-weight-medium">{{ bill.day }} {{ bill.dueDate.toLocaleString('default', { month: 'short' }) }}</span>
                                    </div>
                                </td>
                                <td>
                                    <div class="d-flex flex-column">
                                        <span class="font-weight-medium text-body-2">{{ bill.name }}</span>
                                        <span class="text-caption text-disabled">{{ bill.category }}</span>
                                    </div>
                                </td>
                                <td>
                                    <v-chip size="x-small" variant="outlined" color="primary">
                                        {{ bill.account }}
                                    </v-chip>
                                </td>
                                <td class="text-end font-weight-bold text-body-2">
                                    {{ formatCurrency(bill.amountCents) }}
                                </td>
                                <td class="text-center">
                                    <v-chip
                                        size="x-small"
                                        :color="bill.account === 'Intesa' && intesaShortfall > 0 ? 'error' : 'success'"
                                        variant="tonal"
                                    >
                                        {{ bill.account === 'Intesa' && intesaShortfall > 0 ? tt('Needs Reload') : tt('Covered') }}
                                    </v-chip>
                                </td>
                            </tr>
                        </tbody>
                    </v-table>
                </v-window-item>

                <!-- Tab 3: 30-Day Runway Chart -->
                <v-window-item value="runway">
                    <div style="height: 280px;" class="w-100">
                        <v-chart autoresize :option="runwayChartOptions" class="w-100 h-100" />
                    </div>
                    <div class="d-flex justify-center mt-2 text-caption text-medium-emphasis">
                        <span class="me-4 d-flex align-center">
                            <span class="legend-dot bg-primary me-1"></span>
                            {{ tt('Monthly Budget (Paycheck)') }}
                        </span>
                        <span class="d-flex align-center">
                            <span class="legend-dot bg-error me-1"></span>
                            {{ tt('Intesa Direct Debit Account') }}
                        </span>
                    </div>
                </v-window-item>

                <!-- Tab 4: What-If Simulator -->
                <v-window-item value="whatif">
                    <v-card variant="outlined" class="pa-4 rounded-lg bg-surface-variant-lighten">
                        <div class="text-body-2 font-weight-bold mb-1">
                            {{ tt('Simulate an Unplanned Expense Today') }}
                        </div>
                        <div class="text-caption text-medium-emphasis mb-4">
                            {{ tt('Slide or tap an amount to see how it affects your remaining daily budget for the rest of the paycheck cycle without doing any mental math.') }}
                        </div>

                        <v-row align="center">
                            <v-col cols="12" md="7">
                                <v-slider
                                    v-model="simulatedSpendAmount"
                                    :min="0"
                                    :max="250"
                                    :step="5"
                                    thumb-label="always"
                                    color="primary"
                                    track-color="default"
                                    class="pt-4"
                                >
                                    <template #thumb-label="{ modelValue }">
                                        €{{ modelValue }}
                                    </template>
                                </v-slider>

                                <div class="d-flex gap-2">
                                    <v-btn size="x-small" variant="tonal" class="me-2" @click="simulatedSpendAmount = 20">+€20</v-btn>
                                    <v-btn size="x-small" variant="tonal" class="me-2" @click="simulatedSpendAmount = 50">+€50</v-btn>
                                    <v-btn size="x-small" variant="tonal" class="me-2" @click="simulatedSpendAmount = 100">+€100</v-btn>
                                    <v-btn size="x-small" variant="text" color="error" @click="simulatedSpendAmount = 0">{{ tt('Reset') }}</v-btn>
                                </div>
                            </v-col>

                            <v-col cols="12" md="5">
                                <v-card variant="tonal" :color="simulatedNewDailyAllowance < 1000 ? 'error' : 'primary'" class="pa-3">
                                    <div class="text-caption font-weight-medium">{{ tt('Simulated Remaining Variable Budget') }}</div>
                                    <div class="text-h6 font-weight-bold">{{ formatCurrency(simulatedRemainingBudget) }}</div>

                                    <v-divider class="my-2" />

                                    <div class="text-caption font-weight-medium">{{ tt('New Daily Allowance (Rest of Month)') }}</div>
                                    <div class="d-flex align-baseline">
                                        <span class="text-h5 font-weight-bold">{{ formatCurrency(simulatedNewDailyAllowance) }}</span>
                                        <span class="text-caption ms-1 text-disabled">/ {{ tt('day') }}</span>
                                        <span class="text-caption text-error ms-2" v-if="simulatedSpendAmount > 0">
                                            (-{{ formatCurrency(dailyAllowanceDelta) }}/{{ tt('day') }})
                                        </span>
                                    </div>
                                    <div class="text-caption mt-1">
                                        {{ tt('For') }} {{ daysLeftInCycle }} {{ tt('remaining days until next paycheck') }}
                                    </div>
                                </v-card>
                            </v-col>
                        </v-row>
                    </v-card>
                </v-window-item>
            </v-window>
        </v-card-text>
    </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';

import { useI18n } from '@/locales/helpers.ts';
import { useUserStore } from '@/stores/user.ts';
import { useAccountsStore } from '@/stores/account.ts';
import { useTransactionCategoriesStore } from '@/stores/transactionCategory.ts';
import { useSettingsStore } from '@/stores/setting.ts';
import services from '@/lib/services.ts';
import type { CallbackDataParams } from 'echarts/types/dist/shared';
import type { TransactionInfoResponse } from '@/models/transaction.ts';
import {
    type PendingBill,
    type CycleRange,
    STATIC_MONTHLY_BILLS,
    isDatePayday,
    computeCycle,
    getPaidBillsInCycle,
    getPendingBills,
    getCycleSalary,
    getCycleDailyVariableSpending
} from '@/lib/cashflow.ts';

import {
    mdiCashCheck,
    mdiCalendarClockOutline,
    mdiChartTimelineVariant,
    mdiCalculatorVariantOutline,
    mdiAlertCircleOutline,
    mdiCheckCircleOutline,
    mdiChartAreaspline
} from '@mdi/js';

const props = defineProps<{
    loading: boolean;
    disabled: boolean;
    isDarkMode?: boolean;
}>();

const { tt, formatAmountToLocalizedNumeralsWithCurrency } = useI18n();

const userStore = useUserStore();
const accountsStore = useAccountsStore();
const transactionCategoriesStore = useTransactionCategoriesStore();
const settingsStore = useSettingsStore();

const defaultCurrency = computed<string>(() => userStore.currentUserDefaultCurrency);
const activeTab = ref<string>('pacing');
const simulatedSpendAmount = ref<number>(0);

const today = new Date();

const cycleRange = computed<CycleRange>(() => computeCycle(today));

const priorCycleRange = computed<CycleRange>(() => {
    const dayBeforeStart = new Date(cycleRange.value.start.getTime() - 24 * 60 * 60 * 1000);
    return computeCycle(dayBeforeStart);
});

const totalDaysInCycle = computed(() => cycleRange.value.totalDays);
const currentCycleDay = computed(() => cycleRange.value.currentDay);
const daysLeftInCycle = computed(() => cycleRange.value.daysRemaining);

// Live transaction loading & classification
const cycleTransactions = ref<TransactionInfoResponse[]>([]);
const priorCycleTransactions = ref<TransactionInfoResponse[]>([]);
const isLoadingTransactions = ref<boolean>(false);

async function loadTransactions() {
    isLoadingTransactions.value = true;
    try {
        const priorStartUnix = Math.floor(priorCycleRange.value.start.getTime() / 1000);
        const cycleStartUnix = Math.floor(cycleRange.value.start.getTime() / 1000);
        const cycleEndUnix = Math.floor(cycleRange.value.nextPayday.getTime() / 1000);

        const response = await services.getAllTransactions({
            startTime: priorStartUnix,
            endTime: cycleEndUnix,
            withPictures: false
        });

        if (response.data && response.data.result) {
            const all = response.data.result;
            cycleTransactions.value = all.filter(t => t.time >= cycleStartUnix);
            priorCycleTransactions.value = all.filter(t => t.time >= priorStartUnix && t.time < cycleStartUnix);
        }
    } catch (e) {
        console.error('Failed to load cash flow transactions', e);
    } finally {
        isLoadingTransactions.value = false;
    }
}

watch(() => props.loading, (newVal, oldVal) => {
    if (oldVal && !newVal) {
        loadTransactions();
    }
});

onMounted(() => {
    loadTransactions();
});

// Accounts extraction
const allAccountsList = computed(() => accountsStore.allPlainAccounts || []);

const liquidCash = computed<number>(() => {
    let total = 0;
    for (const acc of allAccountsList.value) {
        if (!acc.hidden && acc.isAsset) {
            // Exclude pure investment accounts from liquid cash
            if (acc.name.toLowerCase().includes('investiti')) {
                continue;
            }
            total += acc.balance || 0;
        }
    }
    return total;
});

const intesaAccount = computed(() =>
    allAccountsList.value.find(acc => acc.name.toLowerCase().includes('intesa'))
);

const intesaBalance = computed<number>(() => intesaAccount.value?.balance || 0);

// Paid bills detection in current cycle
const paidBillsInCycle = computed(() => {
    return getPaidBillsInCycle(
        cycleTransactions.value,
        settingsStore.appSettings.fixedTransactionCategoryFilterInHomePage,
        transactionCategoriesStore.allTransactionCategoriesMap
    );
});

// Pending bills for current cycle
const pendingBills = computed<PendingBill[]>(() => {
    return getPendingBills(paidBillsInCycle.value, cycleRange.value.nextPayday, today);
});

const totalPendingFixed = computed<number>(() => {
    return pendingBills.value.reduce((sum, b) => sum + b.amountCents, 0);
});

// Financial Cash Flow Model: Paycheck Income - Fixed Bills
const currentCycleSalary = computed<number>(() => {
    return getCycleSalary(cycleTransactions.value, priorCycleTransactions.value, cycleRange.value.start);
});

const totalMonthlyFixedBills = computed<number>(() => {
    return STATIC_MONTHLY_BILLS.reduce((sum, b) => sum + b.amountCents, 0);
});

// Discretionary variable budget from salary: e.g. 1736.00 - 1081.07 = 654.93 EUR
const monthlyVariableBudget = computed<number>(() => {
    return Math.max(0, currentCycleSalary.value - totalMonthlyFixedBills.value);
});

// Daily variable spending cumulative tracking
const cycleDailyVariableSpending = computed(() => {
    return getCycleDailyVariableSpending(
        cycleTransactions.value,
        cycleRange.value,
        settingsStore.appSettings.fixedTransactionCategoryFilterInHomePage,
        transactionCategoriesStore.allTransactionCategoriesMap
    );
});

const currentPivotCents = computed<number>(() => {
    const curDay = currentCycleDay.value;
    const { cumulativeSpend } = cycleDailyVariableSpending.value;
    return cumulativeSpend[curDay] ?? 0;
});

// Dynamic Daily Allowance (Row 85: strictly from remaining paycheck variable budget)
const remainingPaycheckVariableBudget = computed<number>(() => {
    return monthlyVariableBudget.value - currentPivotCents.value;
});

const dynamicDailyAllowance = computed<number>(() => {
    const days = daysLeftInCycle.value;
    if (days <= 0 || remainingPaycheckVariableBudget.value <= 0) return 0;
    return Math.round(remainingPaycheckVariableBudget.value / days);
});

// Intesa specific analysis
const intesaPendingBills = computed(() =>
    pendingBills.value.filter(b => b.account === 'Intesa')
);

const intesaPendingTotal = computed<number>(() =>
    intesaPendingBills.value.reduce((sum, b) => sum + b.amountCents, 0)
);

const intesaShortfall = computed<number>(() =>
    Math.max(0, intesaPendingTotal.value - intesaBalance.value)
);

const intesaNextBill = computed(() => intesaPendingBills.value[0]);
const intesaNextBillDateText = computed(() => {
    if (!intesaNextBill.value) return tt('next debit');
    return `${intesaNextBill.value.day} ${intesaNextBill.value.dueDate.toLocaleString('default', { month: 'short' })}`;
});

// Formatting helpers
function formatCurrency(cents: number): string {
    return formatAmountToLocalizedNumeralsWithCurrency(cents, defaultCurrency.value);
}

const displayLiquidCash = computed(() => formatCurrency(liquidCash.value));
const displayPendingFixed = computed(() => formatCurrency(totalPendingFixed.value));
const displayRemainingPaycheckBudget = computed(() => formatCurrency(remainingPaycheckVariableBudget.value));
const displayIntesaBalance = computed(() => formatCurrency(intesaBalance.value));

function getDaysUntilText(daysUntil: number): string {
    if (daysUntil === 0) return tt('Today');
    if (daysUntil === 1) return tt('Tomorrow');
    return `${tt('In')} ${daysUntil} ${tt('days')}`;
}

// What-If Simulator computations
const baseRemainingBudget = computed<number>(() =>
    Math.max(0, remainingPaycheckVariableBudget.value)
);

const simulatedRemainingBudget = computed<number>(() => {
    const extraCents = simulatedSpendAmount.value * 100;
    return Math.max(0, baseRemainingBudget.value - extraCents);
});

const baseDailyAllowance = computed<number>(() => dynamicDailyAllowance.value);

const simulatedNewDailyAllowance = computed<number>(() =>
    daysLeftInCycle.value > 0 ? Math.round(simulatedRemainingBudget.value / daysLeftInCycle.value) : 0
);

const dailyAllowanceDelta = computed<number>(() =>
    baseDailyAllowance.value - simulatedNewDailyAllowance.value
);

// -------------------------------------------------------------
// The 3 Lines of Costs (Excel Rows 67, 68, 69) & Prior Month Ghost
// -------------------------------------------------------------
const cycleDailyBudget = computed(() => {
    return totalDaysInCycle.value > 0 ? (monthlyVariableBudget.value / totalDaysInCycle.value) : 1985;
});

const currentIdealeCents = computed(() => Math.round(currentCycleDay.value * cycleDailyBudget.value));
const pacingDifference = computed(() => currentIdealeCents.value - currentPivotCents.value);

// Prior month daily pace
const priorCycleDailyVariableSpending = computed(() => {
    return getCycleDailyVariableSpending(
        priorCycleTransactions.value,
        priorCycleRange.value,
        settingsStore.appSettings.fixedTransactionCategoryFilterInHomePage,
        transactionCategoriesStore.allTransactionCategoriesMap
    );
});

const priorMonthPaceCents = computed(() => {
    const { cumulativeSpend } = priorCycleDailyVariableSpending.value;
    const curDay = Math.min(currentCycleDay.value, priorCycleRange.value.totalDays);
    const priorAtCur = cumulativeSpend[curDay] ?? 0;
    if (priorAtCur > 0) {
        return priorAtCur;
    }
    return Math.round(currentIdealeCents.value * 0.94);
});

const velocityVsPriorMonth = computed(() => priorMonthPaceCents.value - currentPivotCents.value);

const pacingChartOptions = computed(() => {
    const days = totalDaysInCycle.value;
    const curDay = currentCycleDay.value;
    const dayLabels: string[] = [];
    const idealeData: number[] = [];
    const pivotData: (number | null)[] = [];
    const prevMonthData: number[] = [];

    const startDate = cycleRange.value.start;
    const dailyRateEur = cycleDailyBudget.value / 100;
    const { cumulativeSpend } = cycleDailyVariableSpending.value;

    const priorDays = priorCycleRange.value.totalDays;
    const { cumulativeSpend: priorCum } = priorCycleDailyVariableSpending.value;
    const hasPriorData = (priorCum[priorDays] ?? 0) > 0;

    for (let i = 1; i <= days; i++) {
        const d = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate() + i - 1);
        dayLabels.push(`${d.getDate()} ${d.toLocaleString('default', { month: 'short' })}`);

        const idVal = Math.round(i * dailyRateEur);
        idealeData.push(idVal);

        if (i <= curDay) {
            const pVal = Math.round((cumulativeSpend[i] || 0) / 100);
            pivotData.push(pVal);
        } else {
            pivotData.push(null);
        }

        if (hasPriorData) {
            const pDay = Math.min(i, priorDays);
            prevMonthData.push(Math.round((priorCum[pDay] || 0) / 100));
        } else {
            const prevProg = i / days;
            const prevTotalEur = (monthlyVariableBudget.value / 100) * 0.95;
            prevMonthData.push(Math.round(prevTotalEur * Math.pow(prevProg, 1.05)));
        }
    }

    return {
        tooltip: {
            trigger: 'axis',
            formatter: (params: CallbackDataParams[]) => {
                const first = params[0];
                if (!first) return '';
                let html = `<strong>${first.name} (Day ${(first.dataIndex ?? 0) + 1})</strong><br/>`;
                for (const p of params) {
                    if (p.value !== null && p.value !== undefined) {
                        html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <strong>€${p.value}</strong><br/>`;
                    }
                }
                return html;
            }
        },
        grid: {
            top: 30,
            left: 50,
            right: 20,
            bottom: 25
        },
        xAxis: {
            type: 'category',
            data: dayLabels,
            axisTick: { alignWithLabel: true }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                formatter: '€{value}'
            }
        },
        series: [
            {
                name: tt('Spese Ideali (Row 67)'),
                type: 'line',
                data: idealeData,
                lineStyle: {
                    type: 'dashed',
                    width: 2,
                    color: '#2196F3'
                },
                itemStyle: { color: '#2196F3' }
            },
            {
                name: tt('Spese Pivot (Row 68)'),
                type: 'line',
                data: pivotData,
                lineStyle: {
                    width: 3,
                    color: '#FF9800'
                },
                itemStyle: { color: '#FF9800' },
                areaStyle: {
                    color: 'rgba(255, 152, 0, 0.15)'
                }
            },
            {
                name: tt('Mese Precedente (Row 35 Ghost)'),
                type: 'line',
                data: prevMonthData,
                lineStyle: {
                    type: 'dotted',
                    width: 1.5,
                    color: '#9E9E9E'
                },
                itemStyle: { color: '#9E9E9E' },
                symbol: 'none'
            }
        ]
    };
});

// 30-Day Forward Runway Chart Options: strictly considering monthly budget and not overall portfolio
const runwayChartOptions = computed(() => {
    const dates: string[] = [];
    const budgetSeries: number[] = [];
    const intesaSeries: number[] = [];

    // Monthly Budget runway starts from the remaining paycheck cash (variable budget + pending fixed bills)
    // rather than the overall portfolio savings!
    let currentBudget = (remainingPaycheckVariableBudget.value + totalPendingFixed.value) / 100;
    let currentIntesa = intesaBalance.value / 100;
    const dailyBurnRate = (dynamicDailyAllowance.value > 0 ? dynamicDailyAllowance.value : cycleDailyBudget.value) / 100;

    for (let i = 0; i < 30; i++) {
        const targetDate = new Date(today.getFullYear(), today.getMonth(), today.getDate() + i, 0, 0, 0, 0);
        const dayOfMonth = targetDate.getDate();
        const dateStr = `${dayOfMonth} ${targetDate.toLocaleString('default', { month: 'short' })}`;
        dates.push(dateStr);

        // Check if salary arrives on targetDate (payday: first weekday after 27th)
        if (i > 0 && isDatePayday(targetDate)) {
            currentBudget += (currentCycleSalary.value / 100);
            currentIntesa += 500; // Salary share allocated to Intesa buffer
        }

        // Subtract bills due on this day (for today onwards)
        const billsOnDay = STATIC_MONTHLY_BILLS.filter(b => b.day === dayOfMonth);
        for (const bill of billsOnDay) {
            const isBillApplicable = i > 0 || pendingBills.value.some(p => p.name === bill.name);
            if (isBillApplicable) {
                const billEuros = bill.amountCents / 100;
                currentBudget -= billEuros;
                if (bill.account === 'Intesa') {
                    currentIntesa -= billEuros;
                }
            }
        }

        // Variable daily spend
        currentBudget -= dailyBurnRate;

        budgetSeries.push(Math.round(currentBudget));
        intesaSeries.push(Math.round(currentIntesa));
    }

    return {
        tooltip: {
            trigger: 'axis',
            formatter: (params: CallbackDataParams[]) => {
                const first = params[0];
                if (!first) return '';
                let html = `<strong>${first.name}</strong><br/>`;
                for (const p of params) {
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <strong>€${p.value}</strong><br/>`;
                }
                return html;
            }
        },
        grid: {
            top: 25,
            left: 50,
            right: 20,
            bottom: 25
        },
        xAxis: {
            type: 'category',
            data: dates,
            axisTick: { alignWithLabel: true }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                formatter: '€{value}'
            }
        },
        series: [
            {
                name: tt('Monthly Budget (Paycheck)'),
                type: 'line',
                smooth: true,
                data: budgetSeries,
                color: '#1976D2',
                areaStyle: {
                    color: 'rgba(25, 118, 210, 0.1)'
                }
            },
            {
                name: tt('Intesa Account Buffer'),
                type: 'line',
                smooth: true,
                data: intesaSeries,
                color: '#E53935'
            }
        ]
    };
});
</script>

<style scoped>
.legend-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
}
.border-warning {
    border-color: rgba(251, 140, 0, 0.5) !important;
}
.border-success {
    border-color: rgba(76, 175, 80, 0.5) !important;
}
.border-error {
    border-color: rgba(229, 57, 53, 0.8) !important;
}
</style>

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
                            {{ tt('Checking + Savings + TR Cash') }}
                        </div>
                    </v-card>
                </v-col>

                <v-col cols="12" sm="6" md="3">
                    <v-card variant="outlined" class="pa-3 rounded-lg h-100 border-warning">
                        <span class="text-caption text-medium-emphasis d-block">{{ tt('Pending Fixed Bills') }}</span>
                        <span class="text-h6 font-weight-bold text-warning">{{ displayPendingFixed }}</span>
                        <div class="text-caption text-disabled mt-1">
                            {{ pendingBills.length }} {{ tt('bills due before month-end') }}
                        </div>
                    </v-card>
                </v-col>

                <v-col cols="12" sm="6" md="3">
                    <v-card variant="tonal" color="primary" class="pa-3 rounded-lg h-100">
                        <span class="text-caption font-weight-bold text-uppercase d-block">{{ tt('Safe-to-Spend Cash') }}</span>
                        <span class="text-h6 font-weight-bold">{{ displaySafeToSpend }}</span>
                        <div class="text-caption mt-1">
                            {{ tt('Liquid funds net of pending bills') }}
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
                                {{ tt('Needs +') }}{{ formatCurrency(intesaShortfall + 3000) }} {{ tt('from TR before 20th') }}
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

            <!-- Tab 1: Upcoming Bills Timeline -->
            <v-window v-model="activeTab">
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
                                            {{ getDaysUntilText(bill.daysUntil, bill.day) }}
                                        </v-chip>
                                        <span class="text-body-2 font-weight-medium">{{ bill.day }} Nov</span>
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

                <!-- Tab 2: 30-Day Runway Chart -->
                <v-window-item value="runway">
                    <div style="height: 280px;" class="w-100">
                        <v-chart autoresize :option="runwayChartOptions" class="w-100 h-100" />
                    </div>
                    <div class="d-flex justify-center mt-2 text-caption text-medium-emphasis">
                        <span class="me-4 d-flex align-center">
                            <span class="legend-dot bg-primary me-1"></span>
                            {{ tt('Projected Liquid Cash (All Accounts)') }}
                        </span>
                        <span class="d-flex align-center">
                            <span class="legend-dot bg-error me-1"></span>
                            {{ tt('Intesa Direct Debit Account') }}
                        </span>
                    </div>
                </v-window-item>

                <!-- Tab 3: What-If Simulator -->
                <v-window-item value="whatif">
                    <v-card variant="outlined" class="pa-4 rounded-lg bg-surface-variant-lighten">
                        <div class="text-body-2 font-weight-bold mb-1">
                            {{ tt('Simulate an Unplanned Expense Today') }}
                        </div>
                        <div class="text-caption text-medium-emphasis mb-4">
                            {{ tt('Slide or tap an amount to see how it affects your remaining daily budget for the rest of November without doing any mental math.') }}
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
                                        {{ tt('For') }} {{ daysLeftInThisMonth }} {{ tt('remaining days in November') }}
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
import { ref, computed } from 'vue';

import { useI18n } from '@/locales/helpers.ts';
import { useSettingsStore } from '@/stores/setting.ts';
import { useUserStore } from '@/stores/user.ts';
import { useAccountsStore } from '@/stores/account.ts';
import { useOverviewStore } from '@/stores/overview.ts';

import {
    mdiCashCheck,
    mdiCalendarClockOutline,
    mdiChartTimelineVariant,
    mdiCalculatorVariantOutline,
    mdiAlertCircleOutline,
    mdiCheckCircleOutline
} from '@mdi/js';

defineProps<{
    loading: boolean;
    disabled: boolean;
    isDarkMode?: boolean;
}>();

const { tt, formatAmountToLocalizedNumeralsWithCurrency } = useI18n();

const settingsStore = useSettingsStore();
const userStore = useUserStore();
const accountsStore = useAccountsStore();
const overviewStore = useOverviewStore();

const defaultCurrency = computed<string>(() => userStore.currentUserDefaultCurrency);
const activeTab = ref<string>('timeline');
const simulatedSpendAmount = ref<number>(0);

interface BillDef {
    day: number;
    name: string;
    amountCents: number;
    account: string;
    category: string;
}

const STATIC_MONTHLY_BILLS: BillDef[] = [
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

const today = new Date();
const currentDayOfMonth = today.getDate();
const daysInThisMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
const daysLeftInThisMonth = daysInThisMonth - currentDayOfMonth + 1;

// Accounts extraction
const allAccountsList = computed(() => accountsStore.allPlainAccounts || []);

const liquidCash = computed<number>(() => {
    let total = 0;
    for (const acc of allAccountsList.value) {
        if (!acc.hidden && acc.isAsset) {
            // Exclude pure investment accounts from liquid cash if needed, but include bank/savings/cards
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

// Pending bills for current month
const pendingBills = computed(() => {
    return STATIC_MONTHLY_BILLS
        .filter(bill => bill.day >= currentDayOfMonth)
        .map(bill => ({
            ...bill,
            daysUntil: bill.day - currentDayOfMonth
        }))
        .sort((a, b) => a.day - b.day);
});

const totalPendingFixed = computed<number>(() => {
    return pendingBills.value.reduce((sum, b) => sum + b.amountCents, 0);
});

const safeToSpend = computed<number>(() => {
    return Math.max(0, liquidCash.value - totalPendingFixed.value);
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

// Formatting helpers
function formatCurrency(cents: number): string {
    return formatAmountToLocalizedNumeralsWithCurrency(cents, defaultCurrency.value);
}

const displayLiquidCash = computed(() => formatCurrency(liquidCash.value));
const displayPendingFixed = computed(() => formatCurrency(totalPendingFixed.value));
const displaySafeToSpend = computed(() => formatCurrency(safeToSpend.value));
const displayIntesaBalance = computed(() => formatCurrency(intesaBalance.value));

function getDaysUntilText(daysUntil: number, day: number): string {
    if (daysUntil === 0) return tt('Today');
    if (daysUntil === 1) return tt('Tomorrow');
    return `${tt('In')} ${daysUntil} ${tt('days')}`;
}

// What-If Simulator computations
const monthlyVariableBudget = computed<number>(() => settingsStore.appSettings.monthlyVariableBudgetInHomePage || 72500);
const spentAmountMTD = computed<number>(() => overviewStore.variableExpenseThisMonth?.expenseAmount || 0);

const baseRemainingBudget = computed<number>(() =>
    Math.max(0, monthlyVariableBudget.value - spentAmountMTD.value)
);

const simulatedRemainingBudget = computed<number>(() => {
    const extraCents = simulatedSpendAmount.value * 100;
    return Math.max(0, baseRemainingBudget.value - extraCents);
});

const baseDailyAllowance = computed<number>(() =>
    daysLeftInThisMonth > 0 ? Math.round(baseRemainingBudget.value / daysLeftInThisMonth) : 0
);

const simulatedNewDailyAllowance = computed<number>(() =>
    daysLeftInThisMonth > 0 ? Math.round(simulatedRemainingBudget.value / daysLeftInThisMonth) : 0
);

const dailyAllowanceDelta = computed<number>(() =>
    baseDailyAllowance.value - simulatedNewDailyAllowance.value
);

// 30-Day Forward Runway Chart Options
const runwayChartOptions = computed(() => {
    const dates: string[] = [];
    const liquidSeries: number[] = [];
    const intesaSeries: number[] = [];

    let currentLiquid = liquidCash.value / 100;
    let currentIntesa = intesaBalance.value / 100;
    const dailyBurnRate = (baseDailyAllowance.value / 100) || 16.0;

    for (let i = 0; i < 30; i++) {
        const targetDate = new Date(today.getFullYear(), today.getMonth(), today.getDate() + i);
        const dayOfMonth = targetDate.getDate();
        const dateStr = `${dayOfMonth} ${targetDate.toLocaleString('default', { month: 'short' })}`;
        dates.push(dateStr);

        // Subtract bills due on this day
        const billsOnDay = STATIC_MONTHLY_BILLS.filter(b => b.day === dayOfMonth);
        for (const bill of billsOnDay) {
            const billEuros = bill.amountCents / 100;
            currentLiquid -= billEuros;
            if (bill.account === 'Intesa') {
                currentIntesa -= billEuros;
            }
        }

        // Salary arrival around the 11th
        if (dayOfMonth === 11) {
            currentLiquid += 1704;
            currentIntesa += 500; // typical transfer/allocation
        }

        // Variable daily spend
        currentLiquid -= dailyBurnRate;

        liquidSeries.push(Math.round(currentLiquid));
        intesaSeries.push(Math.round(currentIntesa));
    }

    return {
        tooltip: {
            trigger: 'axis',
            formatter: (params: any[]) => {
                let html = `<strong>${params[0].name}</strong><br/>`;
                for (const p of params) {
                    const color = p.color;
                    html += `<span style="color:${color}">●</span> ${p.seriesName}: <strong>€${p.value}</strong><br/>`;
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
                name: tt('Liquid Balance'),
                type: 'line',
                smooth: true,
                data: liquidSeries,
                color: '#1976D2',
                areaStyle: {
                    color: 'rgba(25, 118, 210, 0.1)'
                }
            },
            {
                name: tt('Intesa Account'),
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

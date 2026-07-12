<template>
    <v-card :class="{ 'disabled': disabled }">
        <v-card-text class="d-flex align-center">
            <v-avatar color="grey" size="38">
                <v-icon size="24" :icon="mdiSpeedometerMedium" />
            </v-avatar>
            <span class="font-weight-bold ms-3">{{ tt('Weekly Variable Spending') }}</span>
            <v-spacer/>
            <v-btn density="comfortable" color="default" variant="text" class="ms-2" :icon="true">
                <v-icon :icon="mdiDotsVertical" />
                <v-menu activator="parent">
                    <v-list>
                        <v-list-item :prepend-icon="mdiListBoxOutline" :to="`/transaction/list?${overviewStore.getTransactionListPageParams({ dateType: DateRange.ThisWeek.type })}`">
                            <v-list-item-title>{{ tt('View Details') }}</v-list-item-title>
                        </v-list-item>
                        <v-list-item :prepend-icon="mdiCogOutline" to="/app/settings">
                            <v-list-item-title>{{ tt('Settings') }}</v-list-item-title>
                        </v-list-item>
                    </v-list>
                </v-menu>
            </v-btn>
        </v-card-text>
        <v-card-text>
            <div class="d-flex align-baseline" v-if="!loading || dataValid">
                <span class="text-truncate text-h4" :class="spentTextColorClass">{{ displaySpentAmount }}</span>
                <span class="text-body-1 ms-2">/ {{ displayWeeklyBudgetAmount }}</span>
            </div>
            <v-skeleton-loader class="skeleton-no-margin mt-4 mb-2" type="text" width="180px" :loading="true" v-else></v-skeleton-loader>

            <v-progress-linear class="mt-3" rounded height="8"
                               :color="paceBarColor"
                               :model-value="spentPercent" />

            <v-row class="mt-2">
                <v-col cols="6">
                    <div class="d-flex flex-column">
                        <span class="text-caption">{{ tt('Daily Average') }}</span>
                        <span class="text-body-1 font-weight-medium" :class="spentTextColorClass" v-if="!loading || dataValid">{{ displayActualDailyAmount }}</span>
                        <v-skeleton-loader class="skeleton-no-margin mt-1" type="text" width="80px" :loading="true" v-else></v-skeleton-loader>
                        <span class="text-caption">{{ tt('format.misc.idealDailyAmount', { amount: displayIdealDailyAmount }) }}</span>
                    </div>
                </v-col>
                <v-col cols="6">
                    <div class="d-flex flex-column">
                        <span class="text-caption">{{ tt('Remaining Budget') }}</span>
                        <span class="text-body-1 font-weight-medium" :class="remainingTextColorClass" v-if="!loading || dataValid">{{ displayRemainingAmount }}</span>
                        <v-skeleton-loader class="skeleton-no-margin mt-1" type="text" width="80px" :loading="true" v-else></v-skeleton-loader>
                        <span class="text-caption">{{ tt('format.misc.availablePerDayForDays', { amount: displayRemainingDailyAmount, count: daysLeftInThisWeek }) }}</span>
                    </div>
                </v-col>
            </v-row>
        </v-card-text>
    </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { useI18n } from '@/locales/helpers.ts';

import { useSettingsStore } from '@/stores/setting.ts';
import { useUserStore } from '@/stores/user.ts';
import { useOverviewStore } from '@/stores/overview.ts';

import { DateRange } from '@/core/datetime.ts';
import { DISPLAY_HIDDEN_AMOUNT, INCOMPLETE_AMOUNT_SUFFIX } from '@/consts/numeral.ts';

import {
    mdiSpeedometerMedium,
    mdiDotsVertical,
    mdiListBoxOutline,
    mdiCogOutline
} from '@mdi/js';

defineProps<{
    loading: boolean;
    disabled: boolean;
}>();

const { tt, formatAmountToLocalizedNumeralsWithCurrency } = useI18n();

const settingsStore = useSettingsStore();
const userStore = useUserStore();
const overviewStore = useOverviewStore();

const showAmountInHomePage = computed<boolean>(() => settingsStore.appSettings.showAmountInHomePage);
const defaultCurrency = computed<string>(() => userStore.currentUserDefaultCurrency);

const monthlyBudgetAmount = computed<number>(() => settingsStore.appSettings.monthlyVariableBudgetInHomePage);
const dataValid = computed<boolean>(() => overviewStore.variableExpenseThisWeek.valid);
const spentAmount = computed<number>(() => overviewStore.variableExpenseThisWeek.expenseAmount);
const incompleteSpentAmount = computed<boolean>(() => overviewStore.variableExpenseThisWeek.incompleteExpenseAmount);

const daysInThisMonth = computed<number>(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
});

const daysInThisWeek = computed<number>(() => {
    const range = overviewStore.transactionDataRange.thisWeek;
    return Math.round((range.endTime - range.startTime + 1) / 86400);
});

const weeklyBudgetAmount = computed<number>(() =>
    Math.round(monthlyBudgetAmount.value * daysInThisWeek.value / daysInThisMonth.value)
);

const dayOfCurrentWeekElapsed = computed<number>(() => {
    const range = overviewStore.transactionDataRange.thisWeek;
    const now = Math.floor(Date.now() / 1000);
    return Math.min(daysInThisWeek.value, Math.floor((now - range.startTime) / 86400) + 1);
});

const daysLeftInThisWeek = computed<number>(() =>
    daysInThisWeek.value - dayOfCurrentWeekElapsed.value + 1
);

const idealSpentToDate = computed<number>(() =>
    Math.round(weeklyBudgetAmount.value * dayOfCurrentWeekElapsed.value / daysInThisWeek.value)
);
const idealDailyAmount = computed<number>(() =>
    Math.round(weeklyBudgetAmount.value / daysInThisWeek.value)
);
const actualDailyAmount = computed<number>(() =>
    Math.round(spentAmount.value / dayOfCurrentWeekElapsed.value)
);
const remainingAmount = computed<number>(() => weeklyBudgetAmount.value - spentAmount.value);
const remainingDailyAmount = computed<number>(() =>
    remainingAmount.value > 0 ? Math.round(remainingAmount.value / daysLeftInThisWeek.value) : 0
);

const spentPercent = computed<number>(() => {
    if (weeklyBudgetAmount.value <= 0) {
        return 0;
    }
    return Math.min(100, spentAmount.value / weeklyBudgetAmount.value * 100);
});

const paceBarColor = computed<string>(() => {
    if (spentAmount.value > weeklyBudgetAmount.value) {
        return 'error';
    } else if (spentAmount.value > idealSpentToDate.value) {
        return 'warning';
    } else {
        return 'success';
    }
});

const spentTextColorClass = computed<string>(() => {
    if (spentAmount.value > weeklyBudgetAmount.value) {
        return 'text-expense';
    } else if (spentAmount.value > idealSpentToDate.value) {
        return 'text-warning';
    } else {
        return 'text-income';
    }
});

const remainingTextColorClass = computed<string>(() => remainingAmount.value < 0 ? 'text-expense' : '');

function getDisplayAmount(amount: number, incomplete?: boolean): string {
    if (!showAmountInHomePage.value) {
        return formatAmountToLocalizedNumeralsWithCurrency(DISPLAY_HIDDEN_AMOUNT, defaultCurrency.value);
    }
    return formatAmountToLocalizedNumeralsWithCurrency(amount, defaultCurrency.value) + (incomplete ? INCOMPLETE_AMOUNT_SUFFIX : '');
}

const displaySpentAmount = computed<string>(() => getDisplayAmount(spentAmount.value, incompleteSpentAmount.value));
const displayWeeklyBudgetAmount = computed<string>(() => getDisplayAmount(weeklyBudgetAmount.value));
const displayActualDailyAmount = computed<string>(() => getDisplayAmount(actualDailyAmount.value));
const displayIdealDailyAmount = computed<string>(() => getDisplayAmount(idealDailyAmount.value));
const displayRemainingAmount = computed<string>(() => getDisplayAmount(remainingAmount.value));
const displayRemainingDailyAmount = computed<string>(() => getDisplayAmount(remainingDailyAmount.value));
</script>

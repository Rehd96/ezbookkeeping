<template>
    <v-card :class="{ 'disabled': disabled }">
        <v-card-item>
            <div class="d-flex align-center flex-wrap">
                <v-avatar color="success" variant="tonal" size="38" class="me-3">
                    <v-icon size="24" :icon="mdiTrendingUp" />
                </v-avatar>
                <div>
                    <v-card-title class="pa-0 text-h6 font-weight-bold">
                        {{ tt('Trade Republic Yield & Investments') }}
                    </v-card-title>
                    <v-card-subtitle class="pa-0 text-caption">
                        {{ tt('2.5% daily accrued interest on cash & portfolio market valuation') }}
                    </v-card-subtitle>
                </div>
                <v-spacer />
                <v-chip color="success" variant="flat" size="small" class="font-weight-bold my-1">
                    +{{ formatDailyInterest(dailyAccruedInterestCents) }} / {{ tt('day') }}
                </v-chip>
            </div>
        </v-card-item>

        <v-card-text class="pt-0">
            <v-row>
                <!-- Left Column: Trade Republic 2.5% Cash Interest Meter -->
                <v-col cols="12" md="6">
                    <v-card variant="outlined" class="pa-4 rounded-lg h-100">
                        <div class="d-flex justify-space-between align-center mb-2">
                            <span class="text-subtitle-2 font-weight-bold">{{ tt('Trade Republic Cash (2.5% p.a.)') }}</span>
                            <v-chip size="x-small" color="primary" variant="tonal">2.50% p.a.</v-chip>
                        </div>

                        <div class="d-flex align-baseline mb-3">
                            <span class="text-h5 font-weight-bold">{{ displayTrCashBalance }}</span>
                            <span class="text-caption text-medium-emphasis ms-2">{{ tt('uninvested cash') }}</span>
                        </div>

                        <v-row class="mb-2">
                            <v-col cols="6">
                                <div class="pa-2 rounded bg-surface-variant-lighten">
                                    <span class="text-caption text-medium-emphasis d-block">{{ tt('Daily Accrual') }}</span>
                                    <span class="text-body-1 font-weight-bold text-success">
                                        +{{ formatDailyInterest(dailyAccruedInterestCents) }}
                                    </span>
                                </div>
                            </v-col>
                            <v-col cols="6">
                                <div class="pa-2 rounded bg-surface-variant-lighten">
                                    <span class="text-caption text-medium-emphasis d-block">{{ tt('Est. Monthly Payout') }}</span>
                                    <span class="text-body-1 font-weight-bold text-success">
                                        +{{ formatCurrency(monthlyProjectedInterestCents) }}
                                    </span>
                                </div>
                            </v-col>
                        </v-row>

                        <!-- Interactive TR Balance Simulator -->
                        <div class="mt-3 pt-2 border-t">
                            <div class="d-flex justify-space-between text-caption text-medium-emphasis mb-1">
                                <span>{{ tt('Interactive Yield Calculator') }}</span>
                                <span class="font-weight-medium">€{{ simulatedTrBalance }}</span>
                            </div>
                            <v-slider
                                v-model="simulatedTrBalance"
                                :min="500"
                                :max="15000"
                                :step="250"
                                density="compact"
                                color="success"
                                hide-details
                            />
                            <div class="text-caption text-disabled mt-1">
                                {{ tt('At') }} €{{ simulatedTrBalance }}: <strong>+{{ (simulatedTrBalance * 0.025 / 365).toFixed(3) }}€/{{ tt('day') }}</strong> (~{{ (simulatedTrBalance * 0.025 / 12).toFixed(2) }}€/{{ tt('mo') }})
                            </div>
                        </div>
                    </v-card>
                </v-col>

                <!-- Right Column: Conto Investimenti Portfolio Reality -->
                <v-col cols="12" md="6">
                    <v-card variant="outlined" class="pa-4 rounded-lg h-100">
                        <div class="d-flex justify-space-between align-center mb-2">
                            <span class="text-subtitle-2 font-weight-bold">{{ tt('Conto Investimenti (Portfolio)') }}</span>
                            <v-btn
                                size="x-small"
                                variant="tonal"
                                color="primary"
                                :prepend-icon="isEditingValuation ? mdiCheck : mdiPencilOutline"
                                @click="toggleEditValuation"
                            >
                                {{ isEditingValuation ? tt('Save') : tt('Update Value') }}
                            </v-btn>
                        </div>

                        <v-row class="mb-3">
                            <v-col cols="6">
                                <span class="text-caption text-medium-emphasis d-block">{{ tt('Cost Basis (PAC Deposits)') }}</span>
                                <span class="text-h6 font-weight-bold">{{ displayInvestedBasis }}</span>
                                <span class="text-caption text-disabled d-block">{{ tt('Sum of transfers') }}</span>
                            </v-col>

                            <v-col cols="6">
                                <span class="text-caption text-medium-emphasis d-block">{{ tt('Current Market Valuation') }}</span>
                                <div v-if="!isEditingValuation" class="d-flex align-baseline">
                                    <span class="text-h6 font-weight-bold">{{ formatCurrency(marketValuationCents) }}</span>
                                </div>
                                <div v-else class="d-flex align-center mt-1">
                                    <v-text-field
                                        v-model="editValuationInput"
                                        density="compact"
                                        variant="outlined"
                                        prefix="€"
                                        type="number"
                                        hide-details
                                        class="valuation-input"
                                        @keyup.enter="saveValuation"
                                    />
                                </div>
                                <span class="text-caption text-disabled d-block">{{ tt('From broker app') }}</span>
                            </v-col>
                        </v-row>

                        <!-- P&L Performance Box -->
                        <div class="pa-3 rounded-lg" :class="isPositivePnl ? 'bg-success-lighten' : 'bg-error-lighten'">
                            <div class="d-flex justify-space-between align-center">
                                <span class="text-caption font-weight-bold text-uppercase">
                                    {{ tt('Unrealized Capital Return (P&L)') }}
                                </span>
                                <span class="text-body-2 font-weight-bold" :class="isPositivePnl ? 'text-success' : 'text-error'">
                                    {{ isPositivePnl ? '+' : '' }}{{ pnlPercent.toFixed(2) }}%
                                </span>
                            </div>
                            <div class="text-h6 font-weight-bold" :class="isPositivePnl ? 'text-success' : 'text-error'">
                                {{ isPositivePnl ? '+' : '' }}{{ formatCurrency(pnlCents) }}
                            </div>
                            <div class="text-caption text-medium-emphasis mt-1">
                                {{ tt('Reflects actual market portfolio value beyond flat cash ledger.') }}
                            </div>
                        </div>
                    </v-card>
                </v-col>
            </v-row>
        </v-card-text>
    </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

import { useI18n } from '@/locales/helpers.ts';
import { useUserStore } from '@/stores/user.ts';
import { useAccountsStore } from '@/stores/account.ts';

import {
    mdiTrendingUp,
    mdiPencilOutline,
    mdiCheck
} from '@mdi/js';

defineProps<{
    loading: boolean;
    disabled: boolean;
}>();

const { tt, formatAmountToLocalizedNumeralsWithCurrency } = useI18n();

const userStore = useUserStore();
const accountsStore = useAccountsStore();
const defaultCurrency = computed<string>(() => userStore.currentUserDefaultCurrency);

const allAccountsList = computed(() => accountsStore.allPlainAccounts || []);

// Trade Republic Cash Account
const trAccount = computed(() =>
    allAccountsList.value.find(acc => acc.name.toLowerCase() === 'trade republic')
);

const trCashBalanceCents = computed<number>(() => trAccount.value?.balance || 0);

// 2.5% rate calculations
const dailyAccruedInterestCents = computed<number>(() => {
    return Math.round((trCashBalanceCents.value * 0.025) / 365);
});

const monthlyProjectedInterestCents = computed<number>(() => {
    return Math.round((trCashBalanceCents.value * 0.025) / 12);
});

const simulatedTrBalance = ref<number>(4500);

// Conto Investimenti Account
const investitiAccount = computed(() =>
    allAccountsList.value.find(acc => acc.name.toLowerCase().includes('investiti'))
);

const investedBasisCents = computed<number>(() => investitiAccount.value?.balance || 43551);

const LOCAL_STORAGE_KEY_VALUATION = 'ezbk_investiti_market_valuation_cents';
const marketValuationCents = ref<number>(48500);
const isEditingValuation = ref<boolean>(false);
const editValuationInput = ref<string>('485.00');

onMounted(() => {
    const saved = localStorage.getItem(LOCAL_STORAGE_KEY_VALUATION);
    if (saved) {
        const val = parseInt(saved, 10);
        if (!isNaN(val) && val > 0) {
            marketValuationCents.value = val;
            editValuationInput.value = (val / 100).toFixed(2);
        }
    } else {
        // default based on recent data
        marketValuationCents.value = investedBasisCents.value || 48500;
        editValuationInput.value = (marketValuationCents.value / 100).toFixed(2);
    }
    simulatedTrBalance.value = Math.round(trCashBalanceCents.value / 100) || 4500;
});

function toggleEditValuation(): void {
    if (isEditingValuation.value) {
        saveValuation();
    } else {
        editValuationInput.value = (marketValuationCents.value / 100).toFixed(2);
        isEditingValuation.value = true;
    }
}

function saveValuation(): void {
    const parsed = parseFloat(editValuationInput.value);
    if (!isNaN(parsed) && parsed >= 0) {
        const cents = Math.round(parsed * 100);
        marketValuationCents.value = cents;
        localStorage.setItem(LOCAL_STORAGE_KEY_VALUATION, cents.toString());
    }
    isEditingValuation.value = false;
}

const pnlCents = computed<number>(() =>
    marketValuationCents.value - investedBasisCents.value
);

const pnlPercent = computed<number>(() => {
    if (investedBasisCents.value <= 0) return 0;
    return (pnlCents.value / investedBasisCents.value) * 100;
});

const isPositivePnl = computed<boolean>(() => pnlCents.value >= 0);

function formatCurrency(cents: number): string {
    return formatAmountToLocalizedNumeralsWithCurrency(cents, defaultCurrency.value);
}

function formatDailyInterest(cents: number): string {
    // for small fractions (e.g. 31.9 cents = €0.32)
    const euros = cents / 100;
    return `€${euros.toFixed(2)}`;
}

const displayTrCashBalance = computed(() => formatCurrency(trCashBalanceCents.value));
const displayInvestedBasis = computed(() => formatCurrency(investedBasisCents.value));
</script>

<style scoped>
.bg-success-lighten {
    background-color: rgba(76, 175, 80, 0.1);
}
.bg-error-lighten {
    background-color: rgba(229, 57, 53, 0.1);
}
.valuation-input {
    max-width: 140px;
}
</style>

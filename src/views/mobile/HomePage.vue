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

        <f7-block-title class="margin-top">{{ tt('Cash Flow & Upcoming Obligations') }}</f7-block-title>
        <f7-card class="cashflow-mobile-card">
            <f7-card-content>
                <div v-if="mobileIntesaShortfall > 0" class="shortfall-alert-box margin-bottom-half">
                    <div class="display-flex align-items-center">
                        <f7-icon f7="exclamationmark_triangle_fill" color="red" class="margin-inline-end-half"></f7-icon>
                        <span class="text-color-red font-weight-bold">{{ tt('Intesa Shortfall') }}: {{ fmt(mobileIntesaShortfall) }}</span>
                    </div>
                    <small class="display-block text-color-red margin-top-quarter">
                        {{ tt('Transfer from TR before') }} {{ mobileIntesaNextBillDateText }}
                    </small>
                </div>
                <div class="display-flex justify-content-space-between align-items-baseline margin-bottom-half">
                    <div>
                        <small class="text-color-gray">{{ tt('Monthly Budget (Paycheck)') }}</small>
                        <div class="text-size-large font-weight-bold" :class="mobileRemainingPaycheckBudget < 0 ? 'text-color-red' : 'text-color-primary'">{{ fmt(mobileRemainingPaycheckBudget) }}</div>
                        <small class="text-color-gray display-block">{{ fmt(mobileDynamicDailyAllowance) }} / {{ tt('day') }} · {{ tt('Fino allo stipendio tra') }} {{ mobileCycleRange.daysRemaining }} {{ tt('giorni') }}</small>
                    </div>
                    <div class="text-align-right">
                        <small class="text-color-gray">{{ tt('Pending Fixed Bills') }}</small>
                        <div class="text-size-large font-weight-bold text-color-orange">{{ fmt(mobileTotalPendingFixed) }}</div>
                        <small class="text-color-gray display-block">{{ mobilePendingBills.length }} {{ tt('bills due before next paycheck') }}</small>
                    </div>
                </div>

                <div class="display-flex justify-content-space-between align-items-baseline margin-top margin-bottom-quarter">
                    <small class="text-color-gray font-weight-medium">{{ tt('Variable Spending') }} ({{ tt('Cycle Day') }} {{ mobileCycleRange.currentDay }}/{{ mobileCycleRange.totalDays }})</small>
                    <span class="font-weight-bold text-size-small" :class="mobilePaceTextColorClass">{{ fmt(mobileCurrentPivotCents) }} / {{ fmt(mobilePaycheckVariableBudget) }}</span>
                </div>
                <f7-progressbar class="budget-bar margin-bottom-quarter" :progress="mobilePaceProgress" :color="mobilePaceBarColor"></f7-progressbar>
                <small class="display-block margin-bottom-half" :class="mobilePaceTextColorClass">{{ mobilePivotDiffText }}</small>

                <div class="display-flex justify-content-space-between text-size-small text-color-gray border-top padding-top-half">
                    <span>{{ tt('Liquid Bank Balance') }}: {{ fmt(mobileLiquidCash) }}</span>
                    <span>Intesa: {{ fmt(mobileIntesaBalance) }}</span>
                </div>
            </f7-card-content>
        </f7-card>

        <f7-block class="no-margin-top margin-bottom-half">
            <f7-segmented strong round>
                <f7-button round :text="tt('Upcoming Bills')" :active="mobileCashflowTab === 'bills'" @click="mobileCashflowTab = 'bills'"></f7-button>
                <f7-button round :text="tt('Cycle Pacing')" :active="mobileCashflowTab === 'pacing'" @click="mobileCashflowTab = 'pacing'"></f7-button>
                <f7-button round :text="tt('What-If Simulator')" :active="mobileCashflowTab === 'whatif'" @click="mobileCashflowTab = 'whatif'"></f7-button>
            </f7-segmented>
        </f7-block>

        <f7-list strong inset dividers class="upcoming-bills-mobile-list no-margin-top" v-if="mobileCashflowTab === 'bills' && mobilePendingBills.length">
            <f7-list-item
                v-for="b in mobilePendingBills"
                :key="b.name + b.day"
                :title="b.name"
                :subtitle="`${b.day} ${b.dueDate.toLocaleString('default', { month: 'short' })} (${getMobileDaysUntilText(b.daysUntil)}) · ${b.account}`"
                :after="fmt(b.amountCents)"
            >
                <template #media>
                    <f7-icon :f7="b.account === 'Intesa' && mobileIntesaShortfall > 0 ? 'exclamationmark_circle_fill' : 'calendar'"
                             :color="b.account === 'Intesa' && mobileIntesaShortfall > 0 ? 'red' : 'primary'"></f7-icon>
                </template>
            </f7-list-item>
        </f7-list>

        <f7-block strong inset class="text-align-center text-color-gray no-margin-top" v-else-if="mobileCashflowTab === 'bills' && !mobilePendingBills.length">
            <f7-icon f7="checkmark_seal_fill" color="green" size="32"></f7-icon>
            <p class="margin-top-half no-margin-bottom">{{ tt('All fixed bills for this cycle are paid') }}</p>
        </f7-block>

        <f7-list strong inset dividers class="pacing-mobile-list no-margin-top" v-else-if="mobileCashflowTab === 'pacing'">
            <f7-list-item :title="tt('Cycle Day')">
                <template #after>
                    <span>{{ mobileCycleRange.currentDay }} / {{ mobileCycleRange.totalDays }}</span>
                </template>
            </f7-list-item>
            <f7-list-item :title="tt('Next Payday')">
                <template #after>
                    <span>{{ mobileNextPaydayFormatted }} ({{ tt('In') }} {{ mobileCycleRange.daysRemaining }} {{ tt('days') }})</span>
                </template>
            </f7-list-item>
            <f7-list-item :title="tt('Detected Salary')">
                <template #after>
                    <span class="text-color-green font-weight-bold">{{ fmt(mobileCycleSalary) }}</span>
                </template>
            </f7-list-item>
            <f7-list-item :title="tt('Total Fixed Bills')">
                <template #after>
                    <span class="text-color-orange">-{{ fmt(mobileTotalMonthlyFixedBills) }}</span>
                </template>
            </f7-list-item>
            <f7-list-item :title="tt('Initial Variable Budget')">
                <template #after>
                    <span class="font-weight-bold">{{ fmt(mobilePaycheckVariableBudget) }}</span>
                </template>
            </f7-list-item>
            <f7-list-item :title="tt('Actual Spend to Date')">
                <template #after>
                    <span :class="mobilePaceTextColorClass" class="font-weight-bold">{{ fmt(mobileCurrentPivotCents) }}</span>
                </template>
            </f7-list-item>
            <f7-list-item :title="tt('Ideal Spend to Date')">
                <template #after>
                    <span>{{ fmt(mobileIdealSpendToDate) }}</span>
                </template>
            </f7-list-item>
            <f7-list-item :title="tt('Pacing Difference')">
                <template #after>
                    <span :class="mobilePaceTextColorClass" class="font-weight-bold">{{ mobilePivotDiffText }}</span>
                </template>
            </f7-list-item>
        </f7-list>

        <f7-card class="whatif-mobile-card no-margin-top" v-else-if="mobileCashflowTab === 'whatif'">
            <f7-card-content>
                <div class="font-weight-bold margin-bottom-quarter">{{ tt('Simulate an Unplanned Expense Today') }}</div>
                <small class="display-block text-color-gray margin-bottom">
                    {{ tt('Slide or tap an amount to see how it affects your remaining daily budget for the rest of the paycheck cycle without doing any mental math.') }}
                </small>

                <div class="whatif-buttons margin-bottom">
                    <f7-button small round outline @click="mobileSimulatedSpendAmount += 20">+€20</f7-button>
                    <f7-button small round outline @click="mobileSimulatedSpendAmount += 50">+€50</f7-button>
                    <f7-button small round outline @click="mobileSimulatedSpendAmount += 100">+€100</f7-button>
                    <f7-button small round outline color="red" @click="mobileSimulatedSpendAmount = 0">{{ tt('Reset') }}</f7-button>
                </div>

                <div class="whatif-result-box">
                    <div class="display-flex justify-content-space-between align-items-center margin-bottom-half">
                        <span class="text-size-small text-color-gray">{{ tt('Simulated Expense') }}</span>
                        <span class="font-weight-bold text-size-large">€{{ mobileSimulatedSpendAmount }}</span>
                    </div>
                    <div class="display-flex justify-content-space-between align-items-center margin-bottom-half">
                        <span class="text-size-small text-color-gray">{{ tt('Simulated Remaining Variable Budget') }}</span>
                        <span class="font-weight-bold" :class="mobileSimulatedRemainingBudget <= 0 ? 'text-color-red' : ''">{{ fmt(mobileSimulatedRemainingBudget) }}</span>
                    </div>
                    <div class="border-top padding-top-half display-flex justify-content-space-between align-items-baseline">
                        <span class="text-size-small text-color-gray">{{ tt('New Daily Allowance (Rest of Month)') }}</span>
                        <div class="text-align-right">
                            <span class="font-weight-bold text-size-large" :class="mobileSimulatedNewDailyAllowance < 1000 ? 'text-color-red' : 'text-color-primary'">
                                {{ fmt(mobileSimulatedNewDailyAllowance) }}
                            </span>
                            <small class="text-color-gray"> / {{ tt('day') }}</small>
                        </div>
                    </div>
                    <small v-if="mobileSimulatedSpendAmount > 0" class="display-block text-align-right text-color-red margin-top-quarter">
                        (-{{ fmt(mobileDailyAllowanceDelta) }}/{{ tt('day') }} {{ tt('For') }} {{ mobileCycleRange.daysRemaining }} {{ tt('remaining days until next paycheck') }})
                    </small>
                </div>
            </f7-card-content>
        </f7-card>

        <f7-block-title>{{ tt('Trade Republic Yield & Investments') }}</f7-block-title>
        <f7-card class="investments-mobile-card">
            <f7-card-content>
                <div class="display-flex justify-content-space-between align-items-baseline margin-bottom-half">
                    <span class="font-weight-bold">Trade Republic (2.5%)</span>
                    <span class="text-color-green font-weight-bold">+{{ (mobileDailyInterest / 100).toFixed(2) }}€ / {{ tt('day') }}</span>
                </div>
                <div class="display-flex justify-content-space-between text-size-small text-color-gray margin-bottom">
                    <span>{{ tt('Cash') }}: {{ fmt(mobileTrCashBalance) }}</span>
                    <span>~{{ fmt(mobileMonthlyInterest) }} / {{ tt('month') }}</span>
                </div>
                <div class="display-flex justify-content-space-between align-items-baseline border-top padding-top-half">
                    <span class="font-weight-bold">Conto Investiti</span>
                    <span :class="mobileIsPositivePnl ? 'text-color-green' : 'text-color-red'" class="font-weight-bold">
                        {{ mobileIsPositivePnl ? '+' : '' }}{{ mobilePnlPercent.toFixed(1) }}% ({{ fmt(mobilePnlCents) }})
                    </span>
                </div>
                <div class="display-flex justify-content-space-between text-size-small text-color-gray">
                    <span>{{ tt('Cost Basis') }}: {{ fmt(mobileInvestedBasis) }}</span>
                    <span>{{ tt('Valuation') }}: {{ fmt(mobileMarketValuation) }}</span>
                </div>
            </f7-card-content>
        </f7-card>

        <f7-block-title v-if="weeklySpendingRows.length || loading">{{ tt('Weekly Spending Breakdown') }}</f7-block-title>
        <f7-list strong inset dividers class="weekly-spending-list" :class="{ 'skeleton-text': loading }" v-if="weeklySpendingRows.length || loading">
            <template v-if="loading">
                <f7-list-item v-for="n in 4" :key="n" title="Loading..." after="..."></f7-list-item>
            </template>
            <template v-else>
                <f7-list-item
                    v-for="row in weeklySpendingRows"
                    :key="row.categoryId"
                    :link="`/transaction/list?categoryIds=${row.categoryId}&dateType=${DateRange.ThisWeek.type}`"
                    :title="row.categoryName"
                    :after="getDisplayWeeklyAmount(row.weekAmount, row.incomplete)"
                ></f7-list-item>
            </template>
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
import services from '@/lib/services.ts';
import type { TransactionInfoResponse } from '@/models/transaction.ts';
import {
    type PendingBill,
    type CycleRange,
    STATIC_MONTHLY_BILLS,
    computeCycle,
    getPaidBillsInCycle,
    getPendingBills,
    getCycleSalary,
    getCycleDailyVariableSpending
} from '@/lib/cashflow.ts';

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

// ── Cash Flow & Upcoming Bills (Mobile) ────────────────────────────────────

const mobileCashflowTab = ref<'bills' | 'pacing' | 'whatif'>('bills');
const mobileSimulatedSpendAmount = ref<number>(0);

const mobileCycleToday = new Date();
const mobileCycleRange = computed<CycleRange>(() => computeCycle(mobileCycleToday));
const mobilePriorCycleRange = computed<CycleRange>(() => {
    const dayBeforeStart = new Date(mobileCycleRange.value.start.getTime() - 24 * 60 * 60 * 1000);
    return computeCycle(dayBeforeStart);
});

const mobileCycleTransactions = ref<TransactionInfoResponse[]>([]);
const mobilePriorCycleTransactions = ref<TransactionInfoResponse[]>([]);
const mobileIsLoadingTransactions = ref<boolean>(false);

async function loadMobileCashFlowTransactions(): Promise<void> {
    mobileIsLoadingTransactions.value = true;
    try {
        const priorStartUnix = Math.floor(mobilePriorCycleRange.value.start.getTime() / 1000);
        const cycleStartUnix = Math.floor(mobileCycleRange.value.start.getTime() / 1000);
        const cycleEndUnix = Math.floor(mobileCycleRange.value.nextPayday.getTime() / 1000);

        const response = await services.getAllTransactions({
            startTime: priorStartUnix,
            endTime: cycleEndUnix,
            withPictures: false
        });

        if (response.data && response.data.result) {
            const all = response.data.result;
            mobileCycleTransactions.value = all.filter(t => t.time >= cycleStartUnix);
            mobilePriorCycleTransactions.value = all.filter(t => t.time >= priorStartUnix && t.time < cycleStartUnix);
        }
    } catch (e) {
        console.error('Failed to load mobile cash flow transactions', e);
    } finally {
        mobileIsLoadingTransactions.value = false;
    }
}

// Paid bills detection in current cycle
const mobilePaidBillsInCycle = computed(() => {
    return getPaidBillsInCycle(
        mobileCycleTransactions.value,
        settingsStore.appSettings.fixedTransactionCategoryFilterInHomePage,
        transactionCategoriesStore.allTransactionCategoriesMap
    );
});

// Pending bills for current cycle
const mobilePendingBills = computed<PendingBill[]>(() => {
    return getPendingBills(mobilePaidBillsInCycle.value, mobileCycleRange.value.nextPayday, mobileCycleToday);
});

function getMobileDaysUntilText(daysUntil: number): string {
    if (daysUntil === 0) return tt('Today');
    if (daysUntil === 1) return tt('Tomorrow');
    return `${tt('In')} ${daysUntil} ${tt('days')}`;
}

const mobileLiquidCash = computed<number>(() => {
    let total = 0;
    for (const acc of accountsStore.allPlainAccounts || []) {
        if (!acc.hidden && acc.isAsset && !acc.name.toLowerCase().includes('investiti')) {
            total += acc.balance || 0;
        }
    }
    return total;
});

const mobileTotalPendingFixed = computed<number>(() =>
    mobilePendingBills.value.reduce((sum, b) => sum + b.amountCents, 0)
);

const mobileCycleSalary = computed<number>(() => {
    return getCycleSalary(mobileCycleTransactions.value, mobilePriorCycleTransactions.value, mobileCycleRange.value.start);
});

const mobileTotalMonthlyFixedBills = computed<number>(() => {
    return STATIC_MONTHLY_BILLS.reduce((sum, b) => sum + b.amountCents, 0);
});

const mobilePaycheckVariableBudget = computed<number>(() => {
    return Math.max(0, mobileCycleSalary.value - mobileTotalMonthlyFixedBills.value);
});

const mobileDailyVariableSpending = computed(() => {
    return getCycleDailyVariableSpending(
        mobileCycleTransactions.value,
        mobileCycleRange.value,
        settingsStore.appSettings.fixedTransactionCategoryFilterInHomePage,
        transactionCategoriesStore.allTransactionCategoriesMap
    );
});

const mobileCurrentPivotCents = computed<number>(() => {
    const curDay = mobileCycleRange.value.currentDay;
    const { cumulativeSpend } = mobileDailyVariableSpending.value;
    return cumulativeSpend[curDay] ?? 0;
});

const mobileRemainingPaycheckBudget = computed<number>(() => {
    return mobilePaycheckVariableBudget.value - mobileCurrentPivotCents.value;
});

const mobileDynamicDailyAllowance = computed<number>(() => {
    const days = mobileCycleRange.value.daysRemaining;
    if (days <= 0 || mobileRemainingPaycheckBudget.value <= 0) return 0;
    return Math.round(mobileRemainingPaycheckBudget.value / days);
});

const mobileIdealSpendToDate = computed<number>(() => {
    const totalDays = mobileCycleRange.value.totalDays;
    const curDay = mobileCycleRange.value.currentDay;
    if (totalDays <= 0) return 0;
    return Math.round(mobilePaycheckVariableBudget.value * (curDay / totalDays));
});

const mobilePivotDifference = computed<number>(() => {
    return mobileIdealSpendToDate.value - mobileCurrentPivotCents.value;
});

const mobilePivotDiffText = computed<string>(() => {
    const diff = mobilePivotDifference.value;
    if (diff >= 0) {
        return `+${fmt(diff)} ${tt('under ideal pace')} (${fmt(mobileIdealSpendToDate.value)})`;
    }
    return `-${fmt(Math.abs(diff))} ${tt('over ideal pace')} (${fmt(mobileIdealSpendToDate.value)})`;
});

const mobilePaceProgress = computed<number>(() => {
    if (mobilePaycheckVariableBudget.value <= 0) return 0;
    return Math.min(100, Math.round((mobileCurrentPivotCents.value / mobilePaycheckVariableBudget.value) * 100));
});

const mobilePaceBarColor = computed<string>(() => {
    if (mobileCurrentPivotCents.value > mobilePaycheckVariableBudget.value) return 'red';
    if (mobileCurrentPivotCents.value > mobileIdealSpendToDate.value) return 'orange';
    return 'green';
});

const mobilePaceTextColorClass = computed<string>(() => {
    if (mobileCurrentPivotCents.value > mobilePaycheckVariableBudget.value) return 'text-color-red';
    if (mobileCurrentPivotCents.value > mobileIdealSpendToDate.value) return 'text-color-orange';
    return 'text-color-green';
});

const mobileNextPaydayFormatted = computed<string>(() => {
    const np = mobileCycleRange.value.nextPayday;
    return `${np.getDate()} ${np.toLocaleString('default', { month: 'short' })}`;
});

const mobileIntesaAccount = computed(() =>
    (accountsStore.allPlainAccounts || []).find(acc => acc.name.toLowerCase().includes('intesa'))
);
const mobileIntesaBalance = computed<number>(() => mobileIntesaAccount.value?.balance || 0);

const mobileIntesaPendingBills = computed(() =>
    mobilePendingBills.value.filter(b => b.account === 'Intesa')
);
const mobileIntesaPendingTotal = computed<number>(() =>
    mobileIntesaPendingBills.value.reduce((sum, b) => sum + b.amountCents, 0)
);
const mobileIntesaShortfall = computed<number>(() =>
    Math.max(0, mobileIntesaPendingTotal.value - mobileIntesaBalance.value)
);
const mobileIntesaNextBill = computed(() => mobileIntesaPendingBills.value[0]);
const mobileIntesaNextBillDateText = computed(() => {
    if (!mobileIntesaNextBill.value) return tt('next debit');
    return `${mobileIntesaNextBill.value.day} ${mobileIntesaNextBill.value.dueDate.toLocaleString('default', { month: 'short' })}`;
});

// What-If Simulator for mobile
const mobileBaseRemainingBudget = computed<number>(() =>
    Math.max(0, mobileRemainingPaycheckBudget.value)
);
const mobileSimulatedRemainingBudget = computed<number>(() => {
    const extraCents = mobileSimulatedSpendAmount.value * 100;
    return Math.max(0, mobileBaseRemainingBudget.value - extraCents);
});
const mobileSimulatedNewDailyAllowance = computed<number>(() => {
    const days = mobileCycleRange.value.daysRemaining;
    if (days <= 0 || mobileSimulatedRemainingBudget.value <= 0) return 0;
    return Math.round(mobileSimulatedRemainingBudget.value / days);
});
const mobileDailyAllowanceDelta = computed<number>(() => {
    return Math.max(0, mobileDynamicDailyAllowance.value - mobileSimulatedNewDailyAllowance.value);
});

// Trade Republic & Investment helpers
const mobileTrAccount = computed(() =>
    (accountsStore.allPlainAccounts || []).find(acc => acc.name.toLowerCase() === 'trade republic')
);
const mobileTrCashBalance = computed<number>(() => mobileTrAccount.value?.balance || 0);
const mobileDailyInterest = computed<number>(() => Math.round((mobileTrCashBalance.value * 0.025) / 365));
const mobileMonthlyInterest = computed<number>(() => Math.round((mobileTrCashBalance.value * 0.025) / 12));

const mobileInvestitiAccount = computed(() =>
    (accountsStore.allPlainAccounts || []).find(acc => acc.name.toLowerCase().includes('investiti'))
);
const mobileInvestedBasis = computed<number>(() => mobileInvestitiAccount.value?.balance || 43551);

const mobileMarketValuation = computed<number>(() => {
    const saved = localStorage.getItem('ezbk_investiti_market_valuation_cents');
    if (saved) {
        const val = parseInt(saved, 10);
        if (!isNaN(val) && val > 0) return val;
    }
    return mobileInvestedBasis.value || 48500;
});
const mobilePnlCents = computed<number>(() => mobileMarketValuation.value - mobileInvestedBasis.value);
const mobilePnlPercent = computed<number>(() =>
    mobileInvestedBasis.value > 0 ? (mobilePnlCents.value / mobileInvestedBasis.value) * 100 : 0
);
const mobileIsPositivePnl = computed<boolean>(() => mobilePnlCents.value >= 0);

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
            overviewStore.loadWeeklyExpenseStatistics({ force: false }),
            loadMobileCashFlowTransactions()
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
        overviewStore.loadWeeklyExpenseStatistics({ force: force }),
        loadMobileCashFlowTransactions()
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

.shortfall-alert-box {
    background-color: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 8px;
    padding: 10px 12px;
}

.whatif-buttons {
    display: flex;
    gap: 8px;
    justify-content: center;
}

.whatif-result-box {
    background-color: rgba(var(--f7-theme-color-rgb, 0, 122, 255), 0.06);
    border-radius: 8px;
    padding: 12px;
}

.dark .whatif-result-box {
    background-color: rgba(255, 255, 255, 0.05);
}
</style>

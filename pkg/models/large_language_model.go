package models

// TransactionTextRecognitionRequest represents the request of recognizing transaction from text
type TransactionTextRecognitionRequest struct {
	Text string `json:"text"`
}

// RecognizedTransactionResponse represents a view-object of recognized transaction response
type RecognizedTransactionResponse struct {
	Type                 TransactionType                       `json:"type"`
	Time                 int64                                 `json:"time,omitempty"`
	CategoryId           int64                                 `json:"categoryId,string,omitempty"`
	SourceAccountId      int64                                 `json:"sourceAccountId,string,omitempty"`
	DestinationAccountId int64                                 `json:"destinationAccountId,string,omitempty"`
	SourceAmount         int64                                 `json:"sourceAmount,omitempty"`
	DestinationAmount    int64                                 `json:"destinationAmount,omitempty"`
	TagIds               []string                              `json:"tagIds,omitempty"`
	Comment              string                                `json:"comment,omitempty"`
	Items                []*RecognizedTransactionItemResponse  `json:"items,omitempty"`
}

// RecognizedTransactionItemResponse represents a view-object of a single recognized line item within a recognized transaction response
type RecognizedTransactionItemResponse struct {
	RawName            string  `json:"rawName"`
	Quantity           float64 `json:"quantity,omitempty"`
	Unit               string  `json:"unit,omitempty"`
	NormalizedQuantity float64 `json:"normalizedQuantity,omitempty"`
	NormalizedUnit     string  `json:"normalizedUnit,omitempty"`
	TotalPrice         int64   `json:"totalPrice,omitempty"`
	StoreName          string  `json:"storeName,omitempty"`
}

// RecognizedTransactionResult represents the result of recognized transaction
type RecognizedTransactionResult struct {
	Type                   string                             `json:"type,omitempty" jsonschema:"enum=income,enum=expense,enum=transfer" jsonschema_description:"Transaction type (income, expense, transfer)"`
	Time                   string                             `json:"time" jsonschema:"format=date-time" jsonschema_description:"Transaction time in long date time format (YYYY-MM-DD HH:mm:ss, e.g. 2023-01-01 12:00:00)"`
	Amount                 string                             `json:"amount,omitempty" jsonschema_description:"Transaction amount"`
	AccountName            string                             `json:"account,omitempty" jsonschema_description:"Account name for the transaction"`
	CategoryName           string                             `json:"category,omitempty" jsonschema_description:"Category name for the transaction"`
	TagNames               []string                           `json:"tags,omitempty" jsonschema_description:"List of tags associated with the transaction (maximum 10 tags allowed)"`
	Description            string                             `json:"description,omitempty" jsonschema_description:"Transaction description"`
	DestinationAmount      string                             `json:"destination_amount,omitempty" jsonschema_description:"Destination amount for transfer transactions"`
	DestinationAccountName string                             `json:"destination_account,omitempty" jsonschema_description:"Destination account name for transfer transactions"`
	Items                  []*RecognizedTransactionItemResult `json:"items,omitempty" jsonschema_description:"Individual line items purchased in this transaction, only populated when item-level receipt recognition is requested"`
}

// RecognizedTransactionItemResult represents a single recognized line item within a transaction (e.g. a receipt row)
type RecognizedTransactionItemResult struct {
	Name       string `json:"name" jsonschema_description:"Item name exactly as printed on the receipt"`
	Quantity   string `json:"quantity,omitempty" jsonschema_description:"Quantity purchased, e.g. 1 or 2.5"`
	Unit       string `json:"unit,omitempty" jsonschema:"enum=L,enum=ml,enum=kg,enum=g,enum=pcs" jsonschema_description:"Unit of measure for the quantity, inferred from the packaging text if not explicit"`
	TotalPrice string `json:"total_price" jsonschema_description:"Total price paid for this line item"`
	StoreName  string `json:"store,omitempty" jsonschema_description:"Merchant or store name, if visible on the receipt"`
}

package models

// TransactionItemNoProductId represents that a transaction item has not been matched to a normalized product yet
const TransactionItemNoProductId = int64(0)

// TransactionItem represents a single line item extracted from a transaction (e.g. a receipt) stored in database
type TransactionItem struct {
	ItemId             int64   `xorm:"PK"`
	Uid                int64   `xorm:"INDEX(IDX_transaction_item_uid_deleted_transaction_id) INDEX(IDX_transaction_item_uid_deleted_product_id_time) NOT NULL"`
	Deleted            bool    `xorm:"INDEX(IDX_transaction_item_uid_deleted_transaction_id) INDEX(IDX_transaction_item_uid_deleted_product_id_time) NOT NULL"`
	TransactionId      int64   `xorm:"INDEX(IDX_transaction_item_uid_deleted_transaction_id) NOT NULL"`
	TransactionTime    int64   `xorm:"INDEX(IDX_transaction_item_uid_deleted_product_id_time) NOT NULL"`
	ProductId          int64   `xorm:"INDEX(IDX_transaction_item_uid_deleted_product_id_time) NOT NULL DEFAULT 0"`
	RawName            string  `xorm:"VARCHAR(255) NOT NULL"`
	Quantity           float64 `xorm:"NOT NULL"`
	Unit               string  `xorm:"VARCHAR(10)"`
	NormalizedQuantity float64 `xorm:"NOT NULL"`
	NormalizedUnit     string  `xorm:"VARCHAR(10) NOT NULL"`
	TotalPrice         int64   `xorm:"NOT NULL"`
	CurrencyCode       string  `xorm:"VARCHAR(3) NOT NULL"`
	StoreName          string  `xorm:"VARCHAR(255)"`
	PictureId          int64   `xorm:"NOT NULL DEFAULT 0"`
	CreatedIp          string  `xorm:"VARCHAR(39)"`
	CreatedUnixTime    int64
	UpdatedUnixTime    int64
	DeletedUnixTime    int64
}

// TransactionItemCreateRequest represents all parameters of a single transaction item within a transaction creation/modification request
type TransactionItemCreateRequest struct {
	ProductId  int64   `json:"productId,string"`
	RawName    string  `json:"rawName" binding:"required,notBlank,max=255"`
	Quantity   float64 `json:"quantity" binding:"required,gt=0"`
	Unit       string  `json:"unit" binding:"max=10"`
	TotalPrice int64   `json:"totalPrice" binding:"min=-99999999999,max=99999999999"`
	StoreName  string  `json:"storeName" binding:"max=255"`
}

// TransactionItemDeleteRequest represents all parameters of transaction item deleting request
type TransactionItemDeleteRequest struct {
	Id int64 `json:"id,string" binding:"required,min=1"`
}

// TransactionItemInfoResponse represents a view-object of transaction item
type TransactionItemInfoResponse struct {
	Id                 int64   `json:"id,string"`
	TransactionId      int64   `json:"transactionId,string"`
	ProductId          int64   `json:"productId,string"`
	RawName            string  `json:"rawName"`
	Quantity           float64 `json:"quantity"`
	Unit               string  `json:"unit"`
	NormalizedQuantity float64 `json:"normalizedQuantity"`
	NormalizedUnit     string  `json:"normalizedUnit"`
	TotalPrice         int64   `json:"totalPrice"`
	CurrencyCode       string  `json:"currencyCode"`
	StoreName          string  `json:"storeName"`
	PictureId          int64   `json:"pictureId,string"`
}

// ToTransactionItemInfoResponse returns a view-object according to database model
func (i *TransactionItem) ToTransactionItemInfoResponse() *TransactionItemInfoResponse {
	return &TransactionItemInfoResponse{
		Id:                 i.ItemId,
		TransactionId:      i.TransactionId,
		ProductId:          i.ProductId,
		RawName:            i.RawName,
		Quantity:           i.Quantity,
		Unit:               i.Unit,
		NormalizedQuantity: i.NormalizedQuantity,
		NormalizedUnit:     i.NormalizedUnit,
		TotalPrice:         i.TotalPrice,
		CurrencyCode:       i.CurrencyCode,
		StoreName:          i.StoreName,
		PictureId:          i.PictureId,
	}
}

// TransactionItemInfoResponseSlice represents the slice data structure of TransactionItemInfoResponse
type TransactionItemInfoResponseSlice []*TransactionItemInfoResponse

// Len returns the count of items
func (s TransactionItemInfoResponseSlice) Len() int {
	return len(s)
}

// Swap swaps two items
func (s TransactionItemInfoResponseSlice) Swap(i, j int) {
	s[i], s[j] = s[j], s[i]
}

// Less reports whether the first item is less than the second one
func (s TransactionItemInfoResponseSlice) Less(i, j int) bool {
	return s[i].Id < s[j].Id
}

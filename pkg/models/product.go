package models

// Product represents a normalized grocery/item product stored in database
type Product struct {
	ProductId       int64  `xorm:"PK"`
	Uid             int64  `xorm:"INDEX(IDX_product_uid_deleted_name) NOT NULL"`
	Deleted         bool   `xorm:"INDEX(IDX_product_uid_deleted_name) NOT NULL"`
	Name            string `xorm:"VARCHAR(100) INDEX(IDX_product_uid_deleted_name) NOT NULL"`
	CategoryId      int64  `xorm:"NOT NULL DEFAULT 0"`
	BaseUnit        string `xorm:"VARCHAR(10) NOT NULL"`
	CreatedUnixTime int64
	UpdatedUnixTime int64
	DeletedUnixTime int64
}

// ProductCreateRequest represents all parameters of product creation request
type ProductCreateRequest struct {
	Name       string `json:"name" binding:"required,notBlank,max=100"`
	CategoryId int64  `json:"categoryId,string"`
	BaseUnit   string `json:"baseUnit" binding:"required,oneof=ml g pcs"`
}

// ProductModifyRequest represents all parameters of product modification request
type ProductModifyRequest struct {
	Id         int64  `json:"id,string" binding:"required,min=1"`
	Name       string `json:"name" binding:"required,notBlank,max=100"`
	CategoryId int64  `json:"categoryId,string"`
	BaseUnit   string `json:"baseUnit" binding:"required,oneof=ml g pcs"`
}

// ProductDeleteRequest represents all parameters of product deleting request
type ProductDeleteRequest struct {
	Id int64 `json:"id,string" binding:"required,min=1"`
}

// ProductInfoResponse represents a view-object of product
type ProductInfoResponse struct {
	Id         int64  `json:"id,string"`
	Name       string `json:"name"`
	CategoryId int64  `json:"categoryId,string"`
	BaseUnit   string `json:"baseUnit"`
}

// ToProductInfoResponse returns a view-object according to database model
func (p *Product) ToProductInfoResponse() *ProductInfoResponse {
	return &ProductInfoResponse{
		Id:         p.ProductId,
		Name:       p.Name,
		CategoryId: p.CategoryId,
		BaseUnit:   p.BaseUnit,
	}
}

// ProductInfoResponseSlice represents the slice data structure of ProductInfoResponse
type ProductInfoResponseSlice []*ProductInfoResponse

// Len returns the count of items
func (s ProductInfoResponseSlice) Len() int {
	return len(s)
}

// Swap swaps two items
func (s ProductInfoResponseSlice) Swap(i, j int) {
	s[i], s[j] = s[j], s[i]
}

// Less reports whether the first item is less than the second one
func (s ProductInfoResponseSlice) Less(i, j int) bool {
	return s[i].Name < s[j].Name
}

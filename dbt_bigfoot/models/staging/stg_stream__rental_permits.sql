select  

	"MainParcel" as parcel_id,
	"AddressDisplay" as full_address,
	"CaseId" as case_id,
	"CaseNumber" as case_number,
	"CaseType" as case_type,
	--"CaseWorkclass" as case_work_class,
	"CaseStatus" as case_status,
	"ProjectName" as project_name,
	"CompanyName" as company_name,
	
	"Description" as description,

	"AddressLine1" as street_number,
	"PreDirection" as street_prefix,
	"AddressLine2" as street_name,
	coalesce("StreetTypeName", "PostDirection") as street_type,
	"City" as city,
	"PostalCode" as zip_code,
	"IsMain" as is_main_address,
	
	"ApplyDate" as apply_date,
	"IssueDate" as issue_date,
	"ExpireDate" as expire_date

from {{ source('raw', 'stream__rental_permits') }}

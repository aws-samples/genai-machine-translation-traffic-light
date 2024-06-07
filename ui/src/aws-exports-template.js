//Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
//SPDX-License-Identifier: MIT-0
const config = {
  oauth: {},
  aws_cognito_username_attributes: [],
  aws_cognito_social_providers: [],
  aws_cognito_signup_attributes: [],
  aws_cognito_mfa_configuration: "OFF",
  aws_cognito_mfa_types: ["SMS"],
  aws_cognito_password_protection_settings: {
    passwordPolicyMinLength: 8,
    passwordPolicyCharacters: [],
  },
  aws_cognito_verification_mechanisms: [],
  aws_appsync_authenticationType: "AMAZON_COGNITO_USER_POOLS",

  aws_project_region: "",
  aws_cognito_region: "",
  aws_appsync_region: "",
  aws_user_files_s3_bucket_region: "",

  aws_user_files_s3_bucket: "",
  aws_cloud_logic_custom: [
    {
      name: "api",
      endpoint: "",
    },
  ],
  aws_user_pools_id: "",
  aws_cognito_identity_pool_id: "",
  aws_user_pools_web_client_id: "",
};

export default config;

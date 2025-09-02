import { neon } from "@neondatabase/serverless";
require("dotenv").config();

const sql = neon(process.env.DATABASE_URL);

exports.handler = async function(event, context) {
  try {
    const result = await sql`SELECT * FROM your_table LIMIT 5`;
    return {
      statusCode: 200,
      body: JSON.stringify(result),
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message }),
    };
  }
};
